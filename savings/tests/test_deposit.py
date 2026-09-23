from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounting.models import Account
from governance.models import GlobalConfig
from ledger.services import account_net_balance
from members.models import Member
from pipeline.services import certify, check
from savings.models import Transaction
from savings.services import deposit
from users.models import UserProfile

User = get_user_model()


class DepositTests(TestCase):
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
            ("2101", "Voluntary Deposits", "LIABILITY"),
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
            first_name="Maria",
            last_name="X",
            national_id="N1",
            phone_number="7",
            date_of_birth="1990-01-01",
            aldeia="A",
            suco="S",
            posto="P",
            municipio="M",
            status=Member.Status.ACTIVE,
        )

    def _run_pipeline(self, txn):
        check(txn.pipeline_actor, self.checker)
        certify(txn.pipeline_actor, self.certifier)

    def test_first_deposit_splits_obligatory_and_voluntary(self):
        txn = deposit(
            member=self.member, amount=Decimal("1000.00"), maker_user=self.maker
        )
        self._run_pipeline(txn)

        txn.refresh_from_db()
        self.assertEqual(txn.status, Transaction.Status.COMPLETED)
        self.assertEqual(txn.obligatory_portion, Decimal("20.00"))
        self.assertEqual(txn.voluntary_portion, Decimal("980.00"))
        self.assertEqual(account_net_balance("1001"), Decimal("1000.00"))
        self.assertEqual(account_net_balance("3101"), Decimal("20.00"))
        self.assertEqual(account_net_balance("2101"), Decimal("980.00"))
