from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone

TWOPLACES = Decimal("0.01")


def round_money(value) -> Decimal:
    return Decimal(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def today():
    return timezone.localdate()
