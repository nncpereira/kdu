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

    assert get_active_value("shu_split") is not None
    assert get_active_value("obligatory_savings_monthly_cap") is not None
