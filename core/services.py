from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone

TWOPLACES = Decimal("0.01")


def round_money(value) -> Decimal:
    return Decimal(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def today():
    return timezone.localdate()
