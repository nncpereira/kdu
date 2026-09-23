from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounting.models import Account
from members.services import onboard_member, pay_initial_capital
from users.models import UserProfile

User = get_user_model()


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
        ]:
            Account.objects.get_or_create(
                account_code=code,
                defaults={"account_name": name, "account_type": atype},
            )

    def test_minimum_capital_enforced(self):
        m = onboard_member(
            first_name="João",
            last_name="Silva",
            phone_number="7",
            date_of_birth="1990-01-01",
            maker_user=self.maker,
        )
        with self.assertRaises(Exception):
            pay_initial_capital(
                member=m, amount=Decimal("40.00"), maker_user=self.maker
            )
