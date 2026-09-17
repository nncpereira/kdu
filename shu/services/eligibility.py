import calendar
from datetime import date
from decimal import Decimal

MONTH_WEIGHTS = {
    7: 12,
    8: 11,
    9: 10,
    10: 9,
    11: 8,
    12: 7,
    1: 6,
    2: 5,
    3: 4,
    4: 3,
    5: 2,
    6: 1,
}


def month_weight(month: int) -> int:
    return MONTH_WEIGHTS[month]


def month_end_dates(fy_start: date, fy_end: date):
    """Yield (year, month, last_day_of_month) for the fiscal year."""
    y, m = fy_start.year, fy_start.month
    while True:
        last = date(y, m, calendar.monthrange(y, m)[1])
        if last > fy_end:
            break
        yield y, m, last
        m += 1
        if m == 13:
            m, y = 1, y + 1


def eligible_months(join_date: date, fy_start: date, fy_end: date):
    """Return {month_end_date: weight} for months the member was active."""
    months = {}
    for y, m, last in month_end_dates(fy_start, fy_end):
        if join_date <= date(y, m, 15):
            months[last] = MONTH_WEIGHTS[m]
    return months


def compute_weighted_units(month_balances):
    """
    month_balances: {month_end_date: (total_balance, weight)}
    Returns (sum_weighted_balance, weighted_savings_units).
    """
    total = Decimal("0")
    for balance, weight in month_balances.values():
        total += Decimal(balance) * weight
    return total, total / Decimal("12")
