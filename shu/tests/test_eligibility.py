from decimal import Decimal
from datetime import date
from django.test import TestCase

from shu.services.eligibility import eligible_months, compute_weighted_units


class EligibilityTests(TestCase):
    def test_full_year_member(self):
        months = eligible_months(
            join_date=date(2024, 5, 10),
            fy_start=date(2025, 7, 1),
            fy_end=date(2026, 6, 30),
        )
        self.assertEqual(len(months), 12)
        weights = sorted(months.values(), reverse=True)
        self.assertEqual(weights[0], 12)  # July
        self.assertEqual(weights[-1], 1)  # June

    def test_joined_mid_month_before_15th(self):
        months = eligible_months(
            join_date=date(2025, 8, 2),
            fy_start=date(2025, 7, 1),
            fy_end=date(2026, 6, 30),
        )
        self.assertEqual(len(months), 11)  # Aug–Jun
        self.assertNotIn(date(2025, 7, 31), months)

    def test_joined_mid_month_after_15th(self):
        months = eligible_months(
            join_date=date(2025, 8, 20),
            fy_start=date(2025, 7, 1),
            fy_end=date(2026, 6, 30),
        )
        self.assertEqual(len(months), 10)  # Sep–Jun

    def test_weighted_units(self):
        # Constant 10,000 for 12 months:
        month_balances = {}
        for m in range(1, 13):
            weight = {
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
            }[m]
            month_balances[date(2025, m, 1)] = (Decimal("10000"), weight)
        total, units = compute_weighted_units(month_balances)
        self.assertEqual(total, Decimal("780000"))
        self.assertEqual(units, Decimal("65000"))
