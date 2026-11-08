from decimal import Decimal

from dispatch.rates import quote


def test_short_light_parcel():
    assert quote(10, 2.0) == Decimal("13.70")
