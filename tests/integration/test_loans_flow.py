"""
Loan origination, manual repayment, scheduled installment waterfall.
"""

from decimal import Decimal

import pytest

from ledger.services import account_net_balance
from loans.models import Loan
from loans.services import originate_loan, repay_manual, repay_scheduled

pytestmark = [pytest.mark.integration, pytest.mark.pipeline]


class TestLoans:
    def test_disbursement(self, db, maker, checker, certifier, maria):
        from tests.helpers import full_pipeline

        loan = originate_loan(
            member=maria,
            principal=Decimal("9000.00"),
            term_months=12,
            monthly_rate=Decimal("0.02"),
            maker_user=maker,
        )
        full_pipeline(loan, checker=checker, certifier=certifier)
        loan.refresh_from_db()

        assert loan.status == Loan.Status.DISBURSED
        assert loan.principal_outstanding == Decimal("9000.00")
        assert account_net_balance("1301") == Decimal("9000.00")

    def test_manual_repayment(self, db, maker, checker, certifier, maria):
        from tests.helpers import full_pipeline

        loan = originate_loan(
            member=maria,
            principal=Decimal("9000.00"),
            term_months=12,
            monthly_rate=Decimal("0.02"),
            maker_user=maker,
        )
        full_pipeline(loan, checker=checker, certifier=certifier)
        loan.refresh_from_db()

        repayment = repay_manual(
            loan=loan,
            principal_paid=Decimal("500.00"),
            interest_paid=Decimal("90.00"),
            maker_user=maker,
        )
        full_pipeline(repayment, checker=checker, certifier=certifier)

        loan.refresh_from_db()
        assert loan.principal_outstanding == Decimal("8500.00")
        assert account_net_balance("40100") == Decimal("90.00")

    def test_scheduled_waterfall_full(self, db, maker, checker, certifier, maria):
        from tests.helpers import full_pipeline

        loan = originate_loan(
            member=maria,
            principal=Decimal("9000.00"),
            term_months=12,
            monthly_rate=Decimal("0.02"),
            maker_user=maker,
        )
        full_pipeline(loan, checker=checker, certifier=certifier)
        loan.refresh_from_db()

        repayment = repay_scheduled(
            loan=loan,
            cash_amount=Decimal("1000.00"),
            scheduled_principal=Decimal("700.00"),
            maker_user=maker,
        )
        full_pipeline(repayment, checker=checker, certifier=certifier)

        loan.refresh_from_db()
        # Interest 180, Principal 700, Oblig 20, Vol 100
        assert loan.principal_outstanding == Decimal("8300.00")
        assert account_net_balance("40100") == Decimal("180.00")
        # The maria fixture seeds Member.kapital_sosial_balance=50 directly
        # (a cache field) with no backing ledger entry, so the real 3101
        # ledger balance only reflects this test's own $20 obligatory credit.
        assert account_net_balance("3101") == Decimal("20.00")
        assert account_net_balance("2101") == Decimal("100.00")

    def test_scheduled_insufficient_for_interest(
        self, db, maker, checker, certifier, maria
    ):
        from tests.helpers import full_pipeline

        loan = originate_loan(
            member=maria,
            principal=Decimal("9000.00"),
            term_months=12,
            monthly_rate=Decimal("0.02"),
            maker_user=maker,
        )
        full_pipeline(loan, checker=checker, certifier=certifier)

        with pytest.raises(Exception):
            repay_scheduled(
                loan=loan,
                cash_amount=Decimal("50.00"),
                scheduled_principal=Decimal("700.00"),
                maker_user=maker,
            )
