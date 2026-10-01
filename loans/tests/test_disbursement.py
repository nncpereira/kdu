from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounting.models import Account
from ledger.services import account_net_balance
from loans.models import Loan
from loans.services import originate_loan
from members.models import Member
from pipeline.services import certify, check
from users.models import UserProfile

User = get_user_model()


class LoanDisbursementTests(TestCase):
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
            ("1301", "Loans Receivable", "ASSET"),
        ]:
            Account.objects.get_or_create(
                account_code=code,
                defaults={"account_name": name, "account_type": atype},
            )

        cls.member = Member.objects.create(
            first_name="Pedro",
            last_name="Z",
            national_id="N3",
            phone_number="9",
            date_of_birth="1990-01-01",
            aldeia="A",
            suco="S",
            posto="P",
            municipio="M",
        )

    def test_disburse_after_pipeline(self):
        loan = originate_loan(
            member=self.member,
            principal=Decimal("9000.00"),
            term_months=12,
            monthly_rate=Decimal("0.02"),
            maker_user=self.maker,
        )
        check(loan.pipeline_actor, self.checker)
        certify(loan.pipeline_actor, self.certifier)

        loan.refresh_from_db()
        self.assertEqual(loan.status, Loan.Status.DISBURSED)
        self.assertEqual(loan.principal_outstanding, Decimal("9000.00"))
        self.assertEqual(account_net_balance("1301"), Decimal("9000.00"))
        self.assertEqual(account_net_balance("1001"), Decimal("-9000.00"))


class LoanApplicationSeasonBlockTests(TestCase):
    """Regression: the board decided loan applications are closed in the
    last two months of the fiscal year (May and June)."""

    @classmethod
    def setUpTestData(cls):
        cls.maker = UserProfile.objects.create(
            user=User.objects.create_user("maker_season"), role=UserProfile.Role.MAKER
        )
        cls.member = Member.objects.create(
            first_name="Pedro", last_name="Z", phone_number="9",
            date_of_birth="1990-01-01", status="Active",
        )

    @patch("loans.services.today", return_value=date(2026, 5, 10))
    def test_blocked_in_may(self, mock_today):
        with self.assertRaises(ValidationError):
            originate_loan(
                member=self.member, principal=Decimal("500.00"), term_months=6,
                monthly_rate=Decimal("0.02"), maker_user=self.maker,
            )

    @patch("loans.services.today", return_value=date(2026, 6, 20))
    def test_blocked_in_june(self, mock_today):
        with self.assertRaises(ValidationError):
            originate_loan(
                member=self.member, principal=Decimal("500.00"), term_months=6,
                monthly_rate=Decimal("0.02"), maker_user=self.maker,
            )

    @patch("loans.services.today", return_value=date(2026, 7, 1))
    def test_allowed_outside_may_june(self, mock_today):
        loan = originate_loan(
            member=self.member, principal=Decimal("500.00"), term_months=6,
            monthly_rate=Decimal("0.02"), maker_user=self.maker,
        )
        self.assertIsNotNone(loan.id)
