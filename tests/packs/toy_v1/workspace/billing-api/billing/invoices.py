"""Invoice arithmetic."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class LineItem:
    description: str
    quantity: int
    unit_price: Decimal


@dataclass
class Invoice:
    number: str
    customer_email: str
    currency: str
    issued: date
    due: date
    items: list[LineItem] = field(default_factory=list)
    paid: Decimal = Decimal("0")


def subtotal(invoice: Invoice) -> Decimal:
    return sum((i.unit_price * i.quantity for i in invoice.items), Decimal("0"))


def total(invoice: Invoice) -> Decimal:
    # TODO(INV-471): round to the currency's minor unit.
    return subtotal(invoice).quantize(Decimal("0.01"))


def amount_due(invoice: Invoice, today: date) -> Decimal:
    return total(invoice) - invoice.paid
