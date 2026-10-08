from __future__ import annotations
import json
import os
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any
from .errors import ValidationError
from .provenance import sha256_json
from .strict_json import loads_strict_json


class InMemoryAppendLedger:
    """Reference ledger interface for tests/examples only; not durable storage."""
    def __init__(self):
        self.records: list[dict[str, Any]] = []
        self.head = "0" * 64
    def append(self, record: Any) -> str:
        payload = asdict(record) if is_dataclass(record) else record
        envelope = {"previous_head": self.head, "record": payload}
        self.head = sha256_json(envelope)
        self.records.append({"previous_head": envelope["previous_head"], "head": self.head, "record": payload})
        return self.head


class JsonlHashLedger:
    """Verified single-writer JSONL appends. Busy/stale writers fail, never auto-retry.

    An exclusive sibling lock file coordinates cooperating processes. A crash can
    leave that lock behind; recovery must be explicit after inspecting the ledger.
    This is not a database transaction with a separately saved atlas document.
    """
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.head, self.count = self.verify()

    @contextmanager
    def _locked(self):
        lock = self.path.with_name(self.path.name + ".lock")
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ValidationError("ledger busy or abandoned lock requires explicit recovery") from exc
        try:
            yield
        finally:
            os.close(fd)
            lock.unlink()

    def append(self, record: Any) -> str:
        payload = asdict(record) if is_dataclass(record) else deepcopy(record)
        with self._locked():
            current_head, current_count = self._verify_unlocked()
            if (current_head, current_count) != (self.head, self.count):
                raise ValidationError("stale ledger writer; reopen after verifying current history")
            envelope = {"sequence": self.count + 1, "previous_head": self.head, "record": payload}
            head = sha256_json(envelope)
            line = dict(envelope, head=head)
            raw = (json.dumps(line, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
            mode = "r+b" if self.path.exists() else "w+b"
            with self.path.open(mode) as handle:
                handle.seek(0, os.SEEK_END)
                original_size = handle.tell()
                try:
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
                except BaseException:
                    # Best-effort rollback for an ordinary write/flush failure.
                    # Power failure and rollback failure remain outside this guarantee.
                    handle.seek(original_size)
                    handle.truncate()
                    handle.flush()
                    raise
            self.head = head
            self.count += 1
            return head

    def _verify_unlocked(self) -> tuple[str, int]:
        if not self.path.exists():
            return "0" * 64, 0
        raw_file = self.path.read_bytes()
        if raw_file and not raw_file.endswith(b"\n"):
            raise ValidationError("ledger ends with an incomplete record")
        previous = "0" * 64
        count = 0
        try:
            lines = raw_file.decode("utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise ValidationError("ledger is not valid UTF-8") from exc
        for line_number, raw in enumerate(lines, 1):
            try:
                item = loads_strict_json(raw)
            except ValidationError as exc:
                raise ValidationError(f"invalid ledger JSON at line {line_number}") from exc
            if not isinstance(item, dict):
                raise ValidationError(f"invalid ledger envelope at line {line_number}")
            if set(item) != {"sequence", "previous_head", "record", "head"}:
                raise ValidationError(f"unexpected or missing ledger envelope fields at line {line_number}")
            count += 1
            if type(item.get("sequence")) is not int or item.get("sequence") != count or item.get("previous_head") != previous:
                raise ValidationError(f"ledger chain/order mismatch at line {line_number}")
            envelope = {"sequence": count, "previous_head": previous, "record": item.get("record")}
            expected = sha256_json(envelope)
            if item.get("head") != expected:
                raise ValidationError(f"ledger digest mismatch at line {line_number}")
            previous = expected
        return previous, count

    def verify(self) -> tuple[str, int]:
        with self._locked():
            return self._verify_unlocked()

    def records(self) -> list[dict[str, Any]]:
        with self._locked():
            self._verify_unlocked()
            if not self.path.exists():
                return []
            return [loads_strict_json(x) for x in self.path.read_text(encoding="utf-8").splitlines()]
