from django.db import migrations

UP_SQL = """
-- ============================================================
-- 0002_ledger_invariants documents Invariant C as guarding only
-- members.kapital_sosial_balance and
-- savings_membervoluntarydeposit.balance_available (both synced
-- exclusively by the certified-journal-entry signal handlers).
-- trg_guard_hold_balance additionally guarded balance_held_pipeline,
-- which the comment never mentions and which no code path was ever
-- built to satisfy: withdraw()/on_withdrawal_certified/
-- on_withdrawal_rejected all set this escrow-hold field directly at
-- maker/certifier time, before any journal entry is certified, and
-- never set app.ledger_posting. Drop the guard on this column.
-- ============================================================
DROP TRIGGER IF EXISTS trg_guard_hold_balance ON savings_membervoluntarydeposit;
"""


DOWN_SQL = """
CREATE TRIGGER trg_guard_hold_balance
    BEFORE UPDATE OF balance_held_pipeline ON savings_membervoluntarydeposit
    FOR EACH ROW
    EXECUTE FUNCTION guard_balance_update('balance_held_pipeline');
"""


class Migration(migrations.Migration):
    dependencies = [
        ("ledger", "0003_guard_balance_allow_noop_update"),
    ]

    operations = [
        migrations.RunSQL(UP_SQL, reverse_sql=DOWN_SQL),
    ]
