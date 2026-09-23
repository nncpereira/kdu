"""
Ledger invariants: double-entry balancing, immutability, reversal.
"""

from decimal import Decimal

import pytest

from ledger.models import JournalEntry
from ledger.services import (
    UnbalancedEntryError,
    account_net_balance,
    post_journal_entry,
    reverse_journal_entry,
)

pytestmark = [pytest.mark.integration, pytest.mark.ledger]


class TestLedgerBasics:
    def test_balanced_entry_created(self, db, maker):
        entry = post_journal_entry(
            description="Deposit test",
            lines=[
                ("1001", "DEBIT", Decimal("100.00")),
                ("3101", "CREDIT", Decimal("100.00")),
            ],
            created_by=maker,
        )
        assert entry.is_balanced
        assert entry.status == JournalEntry.Status.DRAFT

    def test_unbalanced_entry_rejected(self, db, maker):
        with pytest.raises(UnbalancedEntryError):
            post_journal_entry(
                description="Bad",
                lines=[
                    ("1001", "DEBIT", Decimal("100.00")),
                    ("3101", "CREDIT", Decimal("90.00")),
                ],
                created_by=maker,
            )

    def test_certified_entry_is_immutable(self, db, maker, certifier):
        entry = post_journal_entry(
            description="X",
            lines=[
                ("1001", "DEBIT", Decimal("10.00")),
                ("3101", "CREDIT", Decimal("10.00")),
            ],
            created_by=maker,
            auto_certify=True,
            certified_by=certifier,
        )
        with pytest.raises(Exception):
            entry.description = "tampered"
            entry.save(update_fields=["description"])

    def test_reversal_nets_to_zero(self, db, maker, certifier):
        entry = post_journal_entry(
            description="Original",
            lines=[
                ("1001", "DEBIT", Decimal("50.00")),
                ("3101", "CREDIT", Decimal("50.00")),
            ],
            created_by=maker,
            auto_certify=True,
            certified_by=certifier,
        )
        reverse_journal_entry(
            entry,
            created_by=maker,
            reason="wrong",
            auto_certify=True,
            certified_by=certifier,
        )
        assert account_net_balance("1001") == Decimal("0.00")
        assert account_net_balance("3101") == Decimal("0.00")

    def test_double_reversal_blocked(self, db, maker, certifier):
        entry = post_journal_entry(
            description="Original",
            lines=[
                ("1001", "DEBIT", Decimal("50.00")),
                ("3101", "CREDIT", Decimal("50.00")),
            ],
            created_by=maker,
            auto_certify=True,
            certified_by=certifier,
        )
        reverse_journal_entry(
            entry, created_by=maker, auto_certify=True, certified_by=certifier
        )
        with pytest.raises(Exception):
            reverse_journal_entry(
                entry, created_by=maker, auto_certify=True, certified_by=certifier
            )
