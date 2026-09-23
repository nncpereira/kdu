from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounting.models import Account
from ledger.services import account_net_balance
from loans.models import Loan, LoanRepayment
from loans.services import originate_loan, repay_manual
from members.models import Member
from pipeline.services import certify, check
from users.models import UserProfile

User = get_user_model()


class ManualRepaymentTests(TestCase):
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
            ("40100", "Interest Income", "REVENUE"),
        ]:
            Account.objects.get_or_create(
                account_code=code,
                defaults={"account_name": name, "account_type": atype},
            )

        cls.member = Member.objects.create(
            first_name="Maria",
            last_name="Q",
            national_id="N4",
            phone_number="9",
            date_of_birth="1990-01-01",
            aldeia="A",
            suco="S",
            posto="P",
            municipio="M",
        )

    def _disburse(self):
        loan = originate_loan(
            member=self.member,
            principal=Decimal("9000.00"),
            term_months=12,
            monthly_rate=Decimal("0.02"),
            maker_user=self.maker,
        )
        check(loan.pipeline_actor, self.checker)
        certify(loan.pipeline_actor, self.certifier)
        return Loan.objects.get(pk=loan.pk)

    def test_partial_payment_updates_principal(self):
        loan = self._disburse()
        repayment = repay_manual(
            loan=loan,
            principal_paid=Decimal("500.00"),
            interest_paid=Decimal("90.00"),
            maker_user=self.maker,
        )
        check(repayment.pipeline_actor, self.checker)
        certify(repayment.pipeline_actor, self.certifier)

        loan.refresh_from_db()
        repayment.refresh_from_db()
        self.assertEqual(loan.principal_outstanding, Decimal("8500.00"))
        self.assertEqual(repayment.status, LoanRepayment.Status.COMPLETED)
        self.assertEqual(account_net_balance("40100"), Decimal("90.00"))
