from django.db import migrations

UP_SQL = """
-- ============================================================
-- Invariant C (revised): Guard cached balances, but allow
-- no-op updates (e.g. idempotent fixture/data reloads that set
-- the guarded column to its current value) through without
-- requiring app.ledger_posting.
-- ============================================================
CREATE OR REPLACE FUNCTION guard_balance_update()
RETURNS TRIGGER AS $$
DECLARE
    v_column text := TG_ARGV[0];
BEGIN
    IF (to_jsonb(OLD) ->> v_column) IS NOT DISTINCT FROM (to_jsonb(NEW) ->> v_column) THEN
        RETURN NEW;
    END IF;

    IF current_setting('app.ledger_posting', true) IS DISTINCT FROM 'true' THEN
        RAISE EXCEPTION
            'Direct balance updates are forbidden. Use the ledger posting flow.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_guard_member_capital_balance ON members_member;
CREATE TRIGGER trg_guard_member_capital_balance
    BEFORE UPDATE OF kapital_sosial_balance ON members_member
    FOR EACH ROW
    EXECUTE FUNCTION guard_balance_update('kapital_sosial_balance');

DROP TRIGGER IF EXISTS trg_guard_voluntary_balance ON savings_membervoluntarydeposit;
CREATE TRIGGER trg_guard_voluntary_balance
    BEFORE UPDATE OF balance_available ON savings_membervoluntarydeposit
    FOR EACH ROW
    EXECUTE FUNCTION guard_balance_update('balance_available');

DROP TRIGGER IF EXISTS trg_guard_hold_balance ON savings_membervoluntarydeposit;
CREATE TRIGGER trg_guard_hold_balance
    BEFORE UPDATE OF balance_held_pipeline ON savings_membervoluntarydeposit
    FOR EACH ROW
    EXECUTE FUNCTION guard_balance_update('balance_held_pipeline');
"""


DOWN_SQL = """
CREATE OR REPLACE FUNCTION guard_balance_update()
RETURNS TRIGGER AS $$
BEGIN
    IF current_setting('app.ledger_posting', true) IS DISTINCT FROM 'true' THEN
        RAISE EXCEPTION
            'Direct balance updates are forbidden. Use the ledger posting flow.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_guard_member_capital_balance ON members_member;
CREATE TRIGGER trg_guard_member_capital_balance
    BEFORE UPDATE OF kapital_sosial_balance ON members_member
    FOR EACH ROW
    EXECUTE FUNCTION guard_balance_update();

DROP TRIGGER IF EXISTS trg_guard_voluntary_balance ON savings_membervoluntarydeposit;
CREATE TRIGGER trg_guard_voluntary_balance
    BEFORE UPDATE OF balance_available ON savings_membervoluntarydeposit
    FOR EACH ROW
    EXECUTE FUNCTION guard_balance_update();

DROP TRIGGER IF EXISTS trg_guard_hold_balance ON savings_membervoluntarydeposit;
CREATE TRIGGER trg_guard_hold_balance
    BEFORE UPDATE OF balance_held_pipeline ON savings_membervoluntarydeposit
    FOR EACH ROW
    EXECUTE FUNCTION guard_balance_update();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("ledger", "0002_ledger_invariants"),
    ]

    operations = [
        migrations.RunSQL(UP_SQL, reverse_sql=DOWN_SQL),
    ]
