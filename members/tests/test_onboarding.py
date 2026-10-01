from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounting.models import Account
from ledger.services import account_net_balance
from members.models import Member
from members.services import (
    STANDARD_ENTRANCE_FEE,
    STANDARD_FIRST_MONTH_SAVINGS,
    STANDARD_INITIAL_CAPITAL,
    onboard_member,
    pay_initial_capital,
)
from users.models import UserProfile

User = get_user_model()


def _make_active_member(suffix: str) -> Member:
    # Explicit membership_number bypasses generate_membership_number()'s
    # shared sequence, which a per-test autouse fixture resets to zero --
    # that's fine for a test's own members, but collides with members
    # created once in setUpTestData alongside more created per test method.
    return Member.objects.create(
        membership_number=f"KDU-TEST-{suffix}",
        first_name=f"Endorser{suffix}",
        last_name="X",
        phone_number=suffix,
        date_of_birth="1980-01-01",
        status=Member.Status.ACTIVE,
    )


class OnboardingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.maker = UserProfile.objects.create(
            user=User.objects.create_user("maker"), role=UserProfile.Role.MAKER
        )
        cls.checker = UserProfile.objects.create(
            user=User.objects.create_user("checker"), role=UserProfile.Role.CHECKER
        )
        cls.certifier = UserProfile.objects.create(
            user=User.objects.create_user("certifier"),
            role=UserProfile.Role.CERTIFIER,
        )

        for code, name, atype in [
            ("1001", "Cash", "ASSET"),
            ("3101", "Kapital Sosial", "EQUITY"),
            ("40200", "Entrance Fee Income", "REVENUE"),
        ]:
            Account.objects.get_or_create(
                account_code=code,
                defaults={"account_name": name, "account_type": atype},
            )
        cls.endorser_1 = _make_active_member("1")
        cls.endorser_2 = _make_active_member("2")

    def test_minimum_capital_enforced(self):
        m = onboard_member(
            first_name="João",
            last_name="Silva",
            phone_number="7",
            date_of_birth="1990-01-01",
            endorser_1=self.endorser_1,
            endorser_2=self.endorser_2,
            maker_user=self.maker,
        )
        with self.assertRaises(Exception):
            pay_initial_capital(
                member=m, amount=Decimal("40.00"), maker_user=self.maker
            )

    def test_two_distinct_active_endorsers_required(self):
        with self.assertRaises(ValidationError):
            onboard_member(
                first_name="João", last_name="Silva", phone_number="7",
                date_of_birth="1990-01-01",
                endorser_1=self.endorser_1, endorser_2=self.endorser_1,
                maker_user=self.maker,
            )

        inactive = Member.objects.create(
            first_name="Inactive", last_name="X", phone_number="9",
            date_of_birth="1980-01-01", status=Member.Status.SUSPENDED,
        )
        with self.assertRaises(ValidationError):
            onboard_member(
                first_name="João", last_name="Silva", phone_number="7",
                date_of_birth="1990-01-01",
                endorser_1=self.endorser_1, endorser_2=inactive,
                maker_user=self.maker,
            )

    def test_standard_upfront_amount_splits_correctly(self):
        """
        Regression: the board requires $175 upfront from a new member --
        $150 capital + $20 first month's mandatory savings (both build
        Kapital Sosial) + $5 entrance fee (booked as revenue immediately).
        """
        m = onboard_member(
            first_name="João", last_name="Silva", phone_number="7",
            date_of_birth="1990-01-01",
            endorser_1=self.endorser_1, endorser_2=self.endorser_2,
            maker_user=self.maker,
        )
        onboarding = pay_initial_capital(
            member=m,
            amount=STANDARD_INITIAL_CAPITAL,
            first_month_savings=STANDARD_FIRST_MONTH_SAVINGS,
            entrance_fee=STANDARD_ENTRANCE_FEE,
            maker_user=self.maker,
        )
        self.assertEqual(onboarding.initial_capital_amount, Decimal("150.00"))
        self.assertEqual(onboarding.first_month_savings_amount, Decimal("20.00"))
        self.assertEqual(onboarding.entrance_fee_amount, Decimal("5.00"))
        self.assertIsNotNone(onboarding.obligatory_transaction_id)

        from pipeline.services import certify, check

        check(onboarding.pipeline_actor, self.checker)
        certify(onboarding.pipeline_actor, self.certifier)

        m.refresh_from_db()
        self.assertEqual(m.status, Member.Status.ACTIVE)
        self.assertEqual(m.kapital_sosial_balance, Decimal("170.00"))
        self.assertEqual(account_net_balance("40200"), Decimal("5.00"))

        onboarding.obligatory_transaction.refresh_from_db()
        self.assertEqual(onboarding.obligatory_transaction.status, "COMPLETED")


class JuneBlockTests(TestCase):
    """Regression: the board decided no new members are accepted in June."""

    @classmethod
    def setUpTestData(cls):
        cls.maker = UserProfile.objects.create(
            user=User.objects.create_user("maker_june"), role=UserProfile.Role.MAKER
        )
        cls.endorser_1 = _make_active_member("j1")
        cls.endorser_2 = _make_active_member("j2")

    @patch("members.services.today", return_value=date(2026, 6, 15))
    def test_onboarding_blocked_in_june(self, mock_today):
        with self.assertRaises(ValidationError):
            onboard_member(
                first_name="João",
                last_name="Silva",
                phone_number="7",
                date_of_birth="1990-01-01",
                endorser_1=self.endorser_1,
                endorser_2=self.endorser_2,
                maker_user=self.maker,
            )

    @patch("members.services.today", return_value=date(2026, 7, 1))
    def test_onboarding_allowed_outside_june(self, mock_today):
        member = onboard_member(
            first_name="João",
            last_name="Silva",
            phone_number="7",
            date_of_birth="1990-01-01",
            endorser_1=self.endorser_1,
            endorser_2=self.endorser_2,
            maker_user=self.maker,
        )
        self.assertIsNotNone(member.id)
