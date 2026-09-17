from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase

from accounting.models import Account
from members.models import Member
from members.services import request_exit
from users.models import UserProfile

User = get_user_model()


class MemberExitTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.maker = UserProfile.objects.create(
            user=User.objects.create_user("maker"), role=UserProfile.Role.MAKER
        )
        for code, name, atype in [
            ("1001", "Cash", "ASSET"),
            ("3101", "Kapital Sosial", "EQUITY"),
        ]:
            Account.objects.get_or_create(
                account_code=code,
                defaults={"account_name": name, "account_type": atype},
            )

    def test_exit_blocked_when_capital_zero(self):
        m = Member.objects.create(
            first_name="A",
            last_name="B",
            phone_number="1",
            date_of_birth="1990-01-01",
            status=Member.Status.ACTIVE,
            kapital_sosial_balance=Decimal("0.00"),
        )
        with self.assertRaises(Exception):
            request_exit(member=m, maker_user=self.maker)

    def test_exit_creates_refund_je_and_pipeline(self):
        m = Member.objects.create(
            first_name="A",
            last_name="B",
            phone_number="1",
            date_of_birth="1990-01-01",
            status=Member.Status.ACTIVE,
            kapital_sosial_balance=Decimal("500.00"),
        )
        result = request_exit(member=m, maker_user=self.maker)
        self.assertEqual(result.refund_amount, Decimal("500.00"))
        self.assertIsNotNone(result.journal_entry)
        self.assertIsNotNone(result.pipeline_actor)
