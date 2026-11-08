"""Booking validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Booking:
    customer: str
    pickup: date
    distance_km: int
    weight_kg: float


def validate(booking: Booking, today: date) -> list[str]:
    errors = []
    if booking.distance_km <= 0:
        errors.append("distance must be positive")
    return errors
