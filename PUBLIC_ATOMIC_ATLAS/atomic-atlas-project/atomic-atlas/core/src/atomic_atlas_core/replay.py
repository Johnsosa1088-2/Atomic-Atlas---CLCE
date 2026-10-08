from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .errors import RestartBlockedError, ValidationError


class RestartStatus(str, Enum):
    FRESH = "FRESH"
    RESTORED = "RESTORED"
    BLOCKED_SOURCE_MISMATCH = "BLOCKED_SOURCE_MISMATCH"
    BLOCKED_TOPOLOGY_MISMATCH = "BLOCKED_TOPOLOGY_MISMATCH"
    BLOCKED_STATE_MISMATCH = "BLOCKED_STATE_MISMATCH"
    RESET_AFTER_BLOCKED_RESTART = "RESET_AFTER_BLOCKED_RESTART"


@dataclass
class RestartGuard:
    expected_source_digest: str | None = None
    expected_topology_digest: str | None = None
    expected_state_digest: str | None = None
    status: RestartStatus = RestartStatus.FRESH
    reset_reason: str | None = None

    def check(self, *, source_digest: str | None, topology_digest: str | None, state_digest: str | None) -> RestartStatus:
        if self.expected_source_digest is not None and source_digest != self.expected_source_digest:
            self.status = RestartStatus.BLOCKED_SOURCE_MISMATCH
        elif self.expected_topology_digest is not None and topology_digest != self.expected_topology_digest:
            self.status = RestartStatus.BLOCKED_TOPOLOGY_MISMATCH
        elif self.expected_state_digest is not None and state_digest != self.expected_state_digest:
            self.status = RestartStatus.BLOCKED_STATE_MISMATCH
        else:
            self.status = RestartStatus.RESTORED
        return self.status

    def ensure_writable(self) -> None:
        if self.status.value.startswith("BLOCKED_"):
            raise RestartBlockedError("blocked lineage cannot overwrite history")

    def explicit_reset(self, reason: str) -> RestartStatus:
        if not self.status.value.startswith("BLOCKED_"):
            raise ValidationError("reset requires a blocked restart state")
        if not isinstance(reason, str) or not reason.strip():
            raise ValidationError("explicit reset requires a nonempty reason")
        self.reset_reason = reason.strip()
        self.status = RestartStatus.RESET_AFTER_BLOCKED_RESTART
        return self.status
