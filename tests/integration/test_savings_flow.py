"""
Savings deposits and withdrawals through the pipeline.
"""

from decimal import Decimal

import pytest

from core.exceptions import InsufficientBalanceError
from ledger.services import account_net_balance
from pipeline.services import reject
from savings.models import MemberVoluntaryDeposit, Transaction
from savings.services import deposit, withdraw

pytestmark = [pytest.mark.integration, pytest.mark.pipeline]


class TestSavings:
    def test_first_deposit_splits_obligatory_and_voluntary(
        self, db, maker, checker, certifier, maria
    ):
        txn = deposit(member=maria, amount=Decimal("1000.00"), maker_user=maker)
        assert txn.obligatory_portion == Decimal("20.00")
        assert txn.voluntary_portion == Decimal("980.00")

        from tests.helpers import full_pipeline

        full_pipeline(txn, checker=checker, certifier=certifier)

        txn.refresh_from_db()
        maria.refresh_from_db()

        assert txn.status == Transaction.Status.COMPLETED
        assert maria.kapital_sosial_balance == Decimal("70.00")
        assert maria.voluntary_deposit.balance_available == Decimal("980.00")

    def test_second_deposit_all_voluntary(self, db, maker, checker, certifier, maria):
        from tests.helpers import full_pipeline

        t1 = deposit(member=maria, amount=Decimal("1000.00"), maker_user=maker)
        full_pipeline(t1, checker=checker, certifier=certifier)

        t2 = deposit(member=maria, amount=Decimal("500.00"), maker_user=maker)
        assert t2.obligatory_portion == Decimal("0.00")
        assert t2.voluntary_portion == Decimal("500.00")

    def test_withdraw_places_hold_then_releases(
        self, db, maker, checker, certifier, maria
    ):
        from tests.helpers import full_pipeline

        # Fund voluntary account
        t = deposit(member=maria, amount=Decimal("500.00"), maker_user=maker)
        full_pipeline(t, checker=checker, certifier=certifier)

        # Withdrawal
        w = withdraw(member=maria, amount=Decimal("200.00"), maker_user=maker)
        vd = MemberVoluntaryDeposit.objects.get(member=maria)
        assert vd.balance_held_pipeline == Decimal("200.00")

        full_pipeline(w, checker=checker, certifier=certifier)
        vd.refresh_from_db()
        # $500 deposit: $20 obligatory (first this month) + $480 voluntary,
        # then a $200 withdrawal → 480 - 200 = 280.
        assert vd.balance_available == Decimal("280.00")
        assert vd.balance_held_pipeline == Decimal("0.00")

    def test_withdraw_insufficient_rejected(self, db, maker, maria):
        with pytest.raises(InsufficientBalanceError):
            withdraw(member=maria, amount=Decimal("1000.00"), maker_user=maker)

    def test_concurrent_withdrawal_second_blocked(
        self, db, maker, checker, certifier, maria
    ):
        from tests.helpers import full_pipeline

        t = deposit(member=maria, amount=Decimal("1000.00"), maker_user=maker)
        full_pipeline(t, checker=checker, certifier=certifier)

        first = withdraw(member=maria, amount=Decimal("800.00"), maker_user=maker)
        # Second withdrawal should fail because the escrow hold blocks it
        with pytest.raises(InsufficientBalanceError):
            withdraw(member=maria, amount=Decimal("500.00"), maker_user=maker)
