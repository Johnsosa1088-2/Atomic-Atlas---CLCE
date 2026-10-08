from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Iterable, Mapping, Sequence
from .errors import ValidationError
from .model import Relation


@dataclass(frozen=True)
class TraceResult:
    visited: tuple[str, ...]
    status: str
    at: str
    state_changed: bool = False
    transport_occurred: bool = False


def trace_route(route: Sequence[str], relations: Iterable[Relation], *, gates: Mapping[str, bool] | None = None,
                gate_requirements: Mapping[str, str] | None = None,
                cut_edges: Iterable[tuple[str, str]] = ()) -> TraceResult:
    if not route:
        raise ValidationError("trace route cannot be empty")
    declared = set()
    for relation in relations:
        if relation.candidate:
            continue
        declared.add((relation.source, relation.target))
        if not relation.directed or relation.reversible is True:
            declared.add((relation.target, relation.source))
    cuts = {frozenset(pair) for pair in cut_edges}
    requirements = dict(gate_requirements or {})
    supplied = dict(gates or {})
    visited = [route[0]]
    for source, target in zip(route, route[1:]):
        edge = frozenset((source, target))
        if (source, target) not in declared or edge in cuts:
            return TraceResult(tuple(visited), "CUT", target)
        if target in requirements:
            key = requirements[target]
            if key not in supplied or type(supplied[key]) is not bool:
                raise ValidationError(f"explicit boolean gate required: {key}")
            if not supplied[key]:
                return TraceResult(tuple(visited), "HELD", target)
        visited.append(target)
    return TraceResult(tuple(visited), "REACHED_DECLARED_TARGET", route[-1])


def _close_ledger(values: Mapping[str, object], keys: tuple[str, ...], unit: str) -> dict[str, str]:
    if set(values) != set(keys):
        raise ValidationError(f"complete {unit} ledger required")
    try:
        numbers = {k: Decimal(str(values[k])) for k in keys}
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValidationError(f"invalid {unit} value") from exc
    if any(not v.is_finite() or v < 0 for v in numbers.values()):
        raise ValidationError(f"finite nonnegative {unit} values required")
    incoming = numbers[keys[0]]
    # Decimal addition uses the caller's ambient precision. Compare exact
    # rational values so rounding cannot turn an unbalanced ledger into closure.
    outgoing = sum((Fraction(numbers[k]) for k in keys[1:]), Fraction(0))
    if Fraction(incoming) != outgoing:
        raise ValidationError(f"{unit} balance does not close")
    return {k: str(v) for k, v in numbers.items()}


def budget_preview(trace: TraceResult, *, quantities: Mapping[str, Mapping[str, object]], evidence_id: str) -> dict:
    if not isinstance(evidence_id, str) or not evidence_id.strip():
        raise ValidationError("nonempty evidence_id required")
    if trace.status != "REACHED_DECLARED_TARGET":
        return {"status": "NO_BUDGET_ROUTE", "trace": trace.__dict__, "state_changed": False,
                "transport_enabled": False, "evidence_verified": False}
    if not isinstance(quantities, Mapping) or not quantities:
        raise ValidationError("at least one complete budget ledger required")
    closed = {}
    for unit, values in quantities.items():
        if not isinstance(unit, str) or not unit.strip():
            raise ValidationError("nonempty declared budget unit label required")
        if not isinstance(values, Mapping) or any(not isinstance(key, str) or not key.strip() for key in values):
            raise ValidationError("budget buckets must be a mapping with nonempty text labels")
        keys = tuple(values.keys())
        if len(keys) < 2 or keys[0] != "input":
            raise ValidationError("each budget ledger must start with input and contain at least one output bucket")
        closed[unit] = _close_ledger(values, keys, unit)
    return {"status": "ARITHMETIC_CLOSED_HYPOTHESIS", "trace": trace.__dict__, "evidence_id": evidence_id,
            "evidence_verified": False, "closed_ledgers": closed, "state_changed": False,
            "transport_enabled": False, "physical_mechanism_established": False}
