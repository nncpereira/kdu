"""
Governance change workflow through the pipeline.
"""

from decimal import Decimal

import pytest

from core.exceptions import LegalReserveViolationError
from governance.models import GlobalConfig, GlobalConfigChange
from governance.services import propose_change, certify_change

pytestmark = [pytest.mark.integration, pytest.mark.pipeline]


class TestGovernance:
    def test_propose_shu_split_below_25_when_reserve_lt_capital(self, db, maker):
        # Reserve (0) < capital (0 default) → not triggered, so this test
        # needs capital > reserve to trigger the guard.
        from ledger.services import post_journal_entry

        # Seed some capital
        post_journal_entry(
            description="Seed",
            lines=[
                ("1001", "DEBIT", Decimal("1000.00")),
                ("3101", "CREDIT", Decimal("1000.00")),
            ],
            created_by=maker,
            auto_certify=True,
            certified_by=maker,
        )

        with pytest.raises(LegalReserveViolationError):
            propose_change(
                parameter_key="shu_split",
                proposed_value={
                    "reserva_legal_pct": 10,
                    "admin_fund_pct": 30,
                    "jasa_simpanan_pct": 25,
                    "jasa_bunga_pct": 35,
                },
                effective_from="2026-07-01",
                maker_user=maker,
            )

    def test_propose_and_certify_change(self, db, maker, certifier):
        change = propose_change(
            parameter_key="obligatory_savings_monthly_cap",
            proposed_value=25,
            effective_from="2026-07-01",
            maker_user=maker,
        )
        assert change.status == GlobalConfigChange.Status.PENDING_CHECK

        change.status = GlobalConfigChange.Status.PENDING_CERTIFY
        change.save(update_fields=["status"])

        certify_change(change, certifier_user=certifier)

        active = (
            GlobalConfig.objects.filter(
                parameter_key="obligatory_savings_monthly_cap",
                status="ACTIVE",
            )
            .order_by("-effective_from")
            .first()
        )
        assert active.parameter_value == 25
