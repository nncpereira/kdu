from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase

from accounting.models import Account
from core.exceptions import InsufficientBalanceError
from members.models import Member
from pipeline.services import check, certify, reject
from savings.models import MemberVoluntaryDeposit, Transaction
from savings.services import deposit, withdraw
from users.models import UserProfile

User = get_user_model()


class WithdrawTests(TestCase):
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

        cls.member = Member.objects.create(
            first_name="Ana",
            last_name="Y",
            national_id="N2",
            phone_number="8",
            date_of_birth="1990-01-01",
            aldeia="A",
            suco="S",
            posto="P",
            municipio="M",
            status=Member.Status.ACTIVE,
        )

    def _fund_voluntary(self, amount):
        vd = MemberVoluntaryDeposit.objects.create(
            member=self.member, balance_available=amount
        )
        return vd

    def test_withdraw_within_available(self):
        self._fund_voluntary(Decimal("500.00"))
        txn = withdraw(
            member=self.member, amount=Decimal("200.00"), maker_user=self.maker
        )

        # Before certification, only the hold is placed.
        vd = MemberVoluntaryDeposit.objects.get(member=self.member)
        self.assertEqual(vd.balance_held_pipeline, Decimal("200.00"))
        self.assertEqual(vd.balance_available, Decimal("500.00"))

        check(txn.pipeline_actor, self.checker)
        certify(txn.pipeline_actor, self.certifier)

        vd.refresh_from_db()
        self.assertEqual(vd.balance_available, Decimal("300.00"))
        self.assertEqual(vd.balance_held_pipeline, Decimal("0.00"))

    def test_withdraw_insufficient(self):
        self._fund_voluntary(Decimal("100.00"))
        with self.assertRaises(InsufficientBalanceError):
            withdraw(
                member=self.member, amount=Decimal("200.00"), maker_user=self.maker
            )

    def test_reject_releases_hold(self):
        self._fund_voluntary(Decimal("500.00"))
        txn = withdraw(
            member=self.member, amount=Decimal("200.00"), maker_user=self.maker
        )
        reject(txn.pipeline_actor, self.checker, reason="policy")

        vd = MemberVoluntaryDeposit.objects.get(member=self.member)
        self.assertEqual(vd.balance_held_pipeline, Decimal("0.00"))
        self.assertEqual(vd.balance_available, Decimal("500.00"))
