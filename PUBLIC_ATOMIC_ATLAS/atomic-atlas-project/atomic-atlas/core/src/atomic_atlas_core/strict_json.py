"""Unambiguous finite JSON at persisted input boundaries."""
import json
from .errors import ValidationError


def _object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValidationError("duplicate JSON object key: " + key)
        out[key] = value
    return out


def _constant(value):
    raise ValidationError("nonfinite JSON constant prohibited: " + value)


def loads_strict_json(text):
    try:
        return json.loads(text, object_pairs_hook=_object, parse_constant=_constant)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValidationError("invalid persisted JSON") from exc
