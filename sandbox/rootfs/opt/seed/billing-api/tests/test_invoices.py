from datetime import date
from decimal import Decimal

from billing.invoices import Invoice, LineItem, amount_due, total


def make(currency="USD", paid="0"):
    return Invoice("A-1", "a@example.com", currency, date(2027, 1, 1), date(2027, 1, 31),
                   [LineItem("seat", 3, Decimal("19.99"))], Decimal(paid))


def test_total_usd():
    assert total(make()) == Decimal("59.97")


def test_amount_due_subtracts_payments():
    assert amount_due(make(paid="10"), date(2027, 1, 15)) == Decimal("49.97")
