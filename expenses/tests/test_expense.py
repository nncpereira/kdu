from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase

from accounting.models import Account
from expenses.models import Expense
from expenses.services import record_expense
from ledger.services import account_net_balance
from pipeline.services import check, certify
from users.models import UserProfile

User = get_user_model()


class ExpenseTests(TestCase):
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
            ("5101", "AGM Expense", "EXPENSE"),
        ]:
            Account.objects.get_or_create(
                account_code=code,
                defaults={"account_name": name, "account_type": atype},
            )

    def test_record_and_certify_expense(self):
        exp = record_expense(
            description="AGM venue",
            amount=Decimal("6300.00"),
            expense_account_code="5101",
            maker_user=self.maker,
        )
        check(exp.pipeline_actor, self.checker)
        certify(exp.pipeline_actor, self.certifier)

        exp.refresh_from_db()
        self.assertEqual(exp.status, Expense.Status.COMPLETED)
        self.assertEqual(account_net_balance("5101"), Decimal("6300.00"))
        self.assertEqual(account_net_balance("1001"), Decimal("-6300.00"))

    def test_non_expense_account_rejected(self):
        with self.assertRaises(Exception):
            record_expense(
                description="Bad",
                amount=Decimal("100.00"),
                expense_account_code="1001",  # asset, not expense
                maker_user=self.maker,
            )
