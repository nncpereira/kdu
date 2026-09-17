from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase

from accounting.models import Account
from governance.models import GlobalConfig
from shu.models import ShuFiscalYear, ShuCalculation, ShuWeightingBase
from shu.services.calculation import (
    calculate_shu_split,
    run_shu_calculation,
    compute_member_payouts,
)
from members.models import Member
from users.models import UserProfile

User = get_user_model()


class SplitMathTests(TestCase):
    def test_split_sums_exactly_to_surplus(self):
        result = calculate_shu_split(
            Decimal("130461.20"),
            {
                "reserva_legal_pct": 10,
                "admin_fund_pct": 30,
                "jasa_simpanan_pct": 25,
                "jasa_bunga_pct": 35,
            },
        )
        self.assertEqual(sum(result.values()), Decimal("130461.20"))
        self.assertEqual(result["reserva_legal_amt"], Decimal("13046.12"))
        self.assertEqual(result["admin_fund_amt"], Decimal("39138.36"))
        self.assertEqual(result["jasa_simpanan_amt"], Decimal("32615.30"))
        self.assertEqual(result["jasa_bunga_amt"], Decimal("45661.42"))

    def test_rounding_remainder_absorbed(self):
        result = calculate_shu_split(
            Decimal("100.00"),
            {
                "reserva_legal_pct": 33,
                "admin_fund_pct": 33,
                "jasa_simpanan_pct": 17,
                "jasa_bunga_pct": 17,
            },
        )
        self.assertEqual(sum(result.values()), Decimal("100.00"))


class ShuWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.maker = UserProfile.objects.create(
            user=User.objects.create_user("maker"), role=UserProfile.Role.MAKER
        )

        for code, name, atype in [
            ("1001", "Cash", "ASSET"),
            ("3101", "Kapital Sosial", "EQUITY"),
            ("3501", "Reserva Legal", "EQUITY"),
            ("3502", "Admin Fund", "EQUITY"),
            ("3900", "Retained Surplus", "EQUITY"),
            ("3200", "SHU Payable", "LIABILITY"),
        ]:
            Account.objects.get_or_create(
                account_code=code,
                defaults={"account_name": name, "account_type": atype},
            )

        GlobalConfig.objects.create(
            parameter_key="shu_split",
            parameter_value={
                "reserva_legal_pct": 10,
                "admin_fund_pct": 30,
                "jasa_simpanan_pct": 25,
                "jasa_bunga_pct": 35,
            },
            effective_from="2025-01-01",
            status="ACTIVE",
            created_by=cls.maker,
        )

        cls.fy = ShuFiscalYear.objects.create(
            year_start="2025-07-01",
            year_end="2026-06-30",
            net_surplus=Decimal("130461.20"),
            kapital_sosial=Decimal("1259361.74"),
            accumulated_reserva_legal=Decimal("1300000.00"),  # > 100% capital
        )

        cls.member = Member.objects.create(
            first_name="Maria",
            last_name="X",
            phone_number="1",
            date_of_birth="1990-01-01",
            status="Active",
            kapital_sosial_balance=Decimal("10000.00"),
        )

        ShuWeightingBase.objects.create(
            fy=cls.fy,
            member=cls.member,
            sum_weighted_balance=Decimal("780000.00"),
            months_active=12,
            weighted_savings_units=Decimal("65000.00"),
            loan_interest_paid=Decimal("600.00"),
        )

    def test_run_calculation(self):
        calc = run_shu_calculation(fy_id=self.fy.id, maker_user=self.maker)
        self.assertEqual(calc.status, ShuCalculation.Status.PENDING_CHECK)
        self.assertEqual(calc.reserva_legal_amt, Decimal("13046.12"))
        self.assertIsNotNone(calc.pipeline_actor)

    def test_payouts_computed(self):
        calc = run_shu_calculation(fy_id=self.fy.id, maker_user=self.maker)
        count = compute_member_payouts(calc)
        self.assertEqual(count, 1)
        payout = calc.payouts.first()
        # Maria is the only member → she gets the entire Jasa Simpanan + Jasa Bunga pools
        self.assertEqual(payout.jasa_simpanan_gross, Decimal("32615.30"))
        self.assertEqual(payout.jasa_bunga_gross, Decimal("45661.42"))
        self.assertEqual(payout.net_payout, Decimal("78276.72"))
