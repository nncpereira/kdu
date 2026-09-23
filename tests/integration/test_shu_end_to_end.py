"""
End-to-end SHU: snapshot → aggregation → calculation → payout.
"""

from decimal import Decimal

import pytest

from ledger.services import account_net_balance
from shu.models import ShuCalculation, ShuFiscalYear
from shu.services.calculation import compute_member_payouts, run_shu_calculation

pytestmark = [pytest.mark.integration, pytest.mark.shu, pytest.mark.slow]


@pytest.fixture
def seeded_fy(db, maria, ana, pedro):
    from tests.factories import (
        ShuFiscalYearFactory,
        ShuWeightingBaseFactory,
    )

    fy = ShuFiscalYearFactory()

    ShuWeightingBaseFactory(
        fy=fy,
        member=maria,
        sum_weighted_balance=Decimal("780000.00"),
        months_active=12,
        weighted_savings_units=Decimal("65000.00"),
        loan_interest_paid=Decimal("0.00"),
    )
    ShuWeightingBaseFactory(
        fy=fy,
        member=ana,
        sum_weighted_balance=Decimal("330000.00"),
        months_active=11,
        weighted_savings_units=Decimal("27500.00"),
        loan_interest_paid=Decimal("0.00"),
    )
    ShuWeightingBaseFactory(
        fy=fy,
        member=pedro,
        sum_weighted_balance=Decimal("140000.00"),
        months_active=7,
        weighted_savings_units=Decimal("11666.67"),
        loan_interest_paid=Decimal("600.00"),
    )
    return fy


class TestShuFlow:
    def test_calculation_split(self, db, maker, seeded_fy):
        # conftest seeds an equal 25/25/25/25 shu_split (DL 76/2022 Art. 69
        # compliant), so each category gets exactly a quarter of the
        # 130461.20 net surplus.
        calc = run_shu_calculation(fy_id=seeded_fy.id, maker_user=maker)
        assert calc.reserva_legal_amt == Decimal("32615.30")
        assert calc.admin_fund_amt == Decimal("32615.30")
        assert calc.jasa_simpanan_amt == Decimal("32615.30")
        assert calc.jasa_bunga_amt == Decimal("32615.30")

    def test_payouts_sum_to_pool(self, db, maker, seeded_fy):
        calc = run_shu_calculation(fy_id=seeded_fy.id, maker_user=maker)
        count = compute_member_payouts(calc)
        assert count == 3

        total_payout = sum((p.net_payout for p in calc.payouts.all()), Decimal("0"))
        assert total_payout == Decimal("65230.60")

    def test_full_payout_closes_fy(self, db, maker, checker, certifier, seeded_fy):
        from tests.helpers import full_pipeline

        calc = run_shu_calculation(fy_id=seeded_fy.id, maker_user=maker)
        full_pipeline(calc, checker=checker, certifier=certifier)

        calc.refresh_from_db()
        assert calc.status == ShuCalculation.Status.PAYOUT_COMPLETE
        seeded_fy.refresh_from_db()
        assert seeded_fy.status == ShuFiscalYear.Status.CLOSED

        # Payout cash reduced, reserve equity increased
        assert account_net_balance("3501") == Decimal("32615.30")
        assert account_net_balance("3502") == Decimal("32615.30")
