"""
Verify Postgres-level invariants.
"""

from decimal import Decimal

import pytest
from django.db import connection, transaction

from ledger.models import JournalEntry
from ledger.services import post_journal_entry

pytestmark = [pytest.mark.integration, pytest.mark.trigger]


class TestPostgresTriggers:
    def test_double_entry_trigger_blocks_unbalanced(self, db, maker):
        """Bypass service layer to insert directly – trigger should reject."""
        with pytest.raises(Exception):
            with transaction.atomic():
                entry = JournalEntry.objects.create(
                    entry_date="2025-07-01",
                    description="Manual unbalanced",
                    created_by=maker,
                )
                with connection.cursor() as cur:
                    cur.execute(
                        "INSERT INTO ledger_journaltransactionline "
                        "(id, journal_entry_id, account_code, entry_type, amount, created_at) "
                        "VALUES (gen_random_uuid(), %s, '1001', 'DEBIT', 100.00, now())",
                        [entry.id],
                    )
                # The balance trigger is a deferred constraint trigger, so it
                # only runs at commit time or when explicitly forced.
                with connection.cursor() as cur:
                    cur.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_certified_entry_cannot_be_updated(self, db, maker, certifier):
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

    def test_member_balance_guard(self, db, maria):
        with pytest.raises(Exception):
            maria.kapital_sosial_balance = Decimal("999999.00")
            maria.save(update_fields=["kapital_sosial_balance"])

    def test_member_balance_allowed_with_flag(self, db, maria):
        with connection.cursor() as cur:
            cur.execute("SET LOCAL app.ledger_posting = 'true'")
        maria.kapital_sosial_balance = Decimal("100.00")
        maria.save(update_fields=["kapital_sosial_balance"])
        maria.refresh_from_db()
        assert maria.kapital_sosial_balance == Decimal("100.00")
