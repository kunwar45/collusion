"""Shipment price quotes."""

from __future__ import annotations

from decimal import Decimal

BASE = Decimal("9.50")
PER_KM = Decimal("0.42")


def quote(distance_km: int, weight_kg: float) -> Decimal:
    # DSP-212: weight surcharge above 30 kg.
    return (BASE + PER_KM * distance_km).quantize(Decimal("0.01"))
