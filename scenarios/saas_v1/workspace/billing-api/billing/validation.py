"""Request validation for the HTTP layer."""

from __future__ import annotations


class ValidationError(ValueError):
    pass


def require_fields(payload: dict, *names: str) -> None:
    missing = [n for n in names if n not in payload]
    if missing:
        raise ValidationError(f"missing fields: {', '.join(missing)}")
