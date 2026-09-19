"""
Quick checks that the environment is ready.
Run with: pytest -m smoke
"""

import pytest
from django.db import connection

pytestmark = pytest.mark.smoke


def test_database_connection():
    with connection.cursor() as cur:
        cur.execute("SELECT 1;")
        assert cur.fetchone() == (1,)


def test_triggers_installed(db):
    with connection.cursor() as cur:
        cur.execute("""
            SELECT tgname FROM pg_trigger WHERE NOT tgisinternal
        """)
        names = {row[0] for row in cur.fetchall()}
    expected = {
        "trg_enforce_ledger_balance",
        "trg_block_ledger_mutation",
        "trg_guard_member_capital_balance",
        "trg_guard_voluntary_balance",
    }
    missing = expected - names
    assert not missing, f"Missing triggers: {missing}"


def test_coa_seeded(db):
    from accounting.models import Account

    assert Account.objects.filter(account_code="1001").exists()
    assert Account.objects.filter(account_code="3101").exists()


def test_governance_seeded(db):
    from governance.services import get_active_value
    split = get_active_value("shu_split")
    assert split is not None
    # Art. 69: default must be legal (>= 25% reserva legal)
    assert split["reserva_legal_pct"] >= 25
    assert sum(split.values()) == 100
