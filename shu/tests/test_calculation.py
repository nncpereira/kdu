from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounting.models import Account
from governance.models import GlobalConfig
from ledger.services import post_journal_entry
from members.models import Member
from shu.models import ShuCalculation, ShuFiscalYear, ShuWeightingBase
from shu.services.calculation import (
    calculate_shu_split,
    compute_member_payouts,
    create_fiscal_year,
    run_shu_calculation,
)
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


class FyTotalsUseGrossRevenueTests(TestCase):
    """
    Regression: the cooperative's documented practice splits the full
    gross interest income for the year (its own "SHU Cal" spreadsheet's
    "Total Bunga") -- the Admin & Operational Fund share is meant to
    *fund* expenses, not have them netted out beforehand. Confirmed
    against real historical data during a members import: with real
    interest income and a real recorded expense, _compute_fy_totals()
    must return net_surplus == total_revenue, not revenue minus expenses.
    """

    @classmethod
    def setUpTestData(cls):
        cls.maker = UserProfile.objects.create(
            user=User.objects.create_user("maker2"), role=UserProfile.Role.MAKER
        )
        for code, name, atype in [
            ("1001", "Cash", "ASSET"),
            ("3101", "Kapital Sosial", "EQUITY"),
            ("40100", "Interest Income from Loans", "REVENUE"),
            ("5101", "AGM Expense", "EXPENSE"),
        ]:
            Account.objects.get_or_create(
                account_code=code,
                defaults={"account_name": name, "account_type": atype},
            )

    def test_net_surplus_is_gross_revenue_not_revenue_minus_expenses(self):
        post_journal_entry(
            description="Interest income",
            lines=[("1001", "DEBIT", Decimal("1000.00")), ("40100", "CREDIT", Decimal("1000.00"))],
            created_by=self.maker, entry_date="2025-08-01",
            auto_certify=True, certified_by=self.maker,
        )
        post_journal_entry(
            description="AGM expense",
            lines=[("5101", "DEBIT", Decimal("300.00")), ("1001", "CREDIT", Decimal("300.00"))],
            created_by=self.maker, entry_date="2025-09-01",
            auto_certify=True, certified_by=self.maker,
        )

        fy = create_fiscal_year("2025-07-01", "2026-06-30")

        self.assertEqual(fy.net_surplus, Decimal("1000.00"))


class AnnualFeeDeductionTests(TestCase):
    """
    Regression: the Member Booklet's own payslip formula is
    Final Payout = (Jasa Simpanan + Jasa Bunga) - Annual KDU Fee - ...,
    but compute_member_payouts() used to pay out the gross amount with
    no deduction at all. shu_annual_fee is a governance-configurable
    flat fee, deducted per member and floored at zero (never negative).
    """

    @classmethod
    def setUpTestData(cls):
        cls.maker = UserProfile.objects.create(
            user=User.objects.create_user("maker3"), role=UserProfile.Role.MAKER
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
                "reserva_legal_pct": 10, "admin_fund_pct": 30,
                "jasa_simpanan_pct": 25, "jasa_bunga_pct": 35,
            },
            effective_from="2025-01-01", status="ACTIVE", created_by=cls.maker,
        )
        GlobalConfig.objects.create(
            parameter_key="shu_annual_fee",
            parameter_value="20.00",
            effective_from="2025-01-01", status="ACTIVE", created_by=cls.maker,
        )

        cls.fy = ShuFiscalYear.objects.create(
            year_start="2025-07-01", year_end="2026-06-30",
            net_surplus=Decimal("1000.00"),
            kapital_sosial=Decimal("0.00"),
            accumulated_reserva_legal=Decimal("0.00"),
        )

        cls.regular_member = Member.objects.create(
            first_name="Maria", last_name="X", phone_number="1",
            date_of_birth="1990-01-01", status="Active",
        )
        ShuWeightingBase.objects.create(
            fy=cls.fy, member=cls.regular_member,
            sum_weighted_balance=Decimal("11400.00"), months_active=12,
            weighted_savings_units=Decimal("950.00"), loan_interest_paid=Decimal("0.00"),
        )

        # A member whose gross share is smaller than the flat fee.
        cls.small_member = Member.objects.create(
            first_name="Small", last_name="Saver", phone_number="2",
            date_of_birth="1990-01-01", status="Active",
        )
        ShuWeightingBase.objects.create(
            fy=cls.fy, member=cls.small_member,
            sum_weighted_balance=Decimal("60.00"), months_active=12,
            weighted_savings_units=Decimal("5.00"), loan_interest_paid=Decimal("0.00"),
        )

    def test_fee_is_deducted_from_net_payout(self):
        calc = run_shu_calculation(fy_id=self.fy.id, maker_user=self.maker)
        compute_member_payouts(calc)

        payout = calc.payouts.get(member=self.regular_member)
        self.assertEqual(payout.annual_fee_deducted, Decimal("20.00"))
        self.assertEqual(
            payout.net_payout,
            payout.jasa_simpanan_gross + payout.jasa_bunga_gross - Decimal("20.00"),
        )

    def test_fee_floors_at_zero_never_goes_negative(self):
        calc = run_shu_calculation(fy_id=self.fy.id, maker_user=self.maker)
        compute_member_payouts(calc)

        payout = calc.payouts.get(member=self.small_member)
        gross = payout.jasa_simpanan_gross + payout.jasa_bunga_gross
        self.assertLess(gross, Decimal("20.00"))
        self.assertEqual(payout.annual_fee_deducted, gross)
        self.assertEqual(payout.net_payout, Decimal("0.00"))
