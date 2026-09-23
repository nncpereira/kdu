from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounting.models import Account
from governance.models import GlobalConfig
from loans.services import originate_loan, repay_scheduled
from members.models import Member
from pipeline.services import certify, check
from users.models import UserProfile

User = get_user_model()


class ScheduledInstallmentTests(TestCase):
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
            ("2101", "Voluntary Deposits", "LIABILITY"),
            ("3101", "Kapital Sosial", "EQUITY"),
            ("40100", "Interest Income", "REVENUE"),
        ]:
            Account.objects.get_or_create(
                account_code=code,
                defaults={"account_name": name, "account_type": atype},
            )

        GlobalConfig.objects.create(
            parameter_key="obligatory_savings_monthly_cap",
            parameter_value=20,
            effective_from="2025-01-01",
            status="ACTIVE",
            created_by=cls.maker,
        )

        cls.member = Member.objects.create(
            first_name="Pedro",
            last_name="Z",
            national_id="N5",
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
        return loan.__class__.objects.get(pk=loan.pk)

    def test_full_waterfall(self):
        loan = self._disburse()
        repayment = repay_scheduled(
            loan=loan,
            cash_amount=Decimal("1000.00"),
            scheduled_principal=Decimal("700.00"),
            maker_user=self.maker,
        )
        check(repayment.pipeline_actor, self.checker)
        certify(repayment.pipeline_actor, self.certifier)

        loan.refresh_from_db()
        # interest 180, principal 700, oblig 20, voluntary 100
        self.assertEqual(loan.principal_outstanding, Decimal("8300.00"))
