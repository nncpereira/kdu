from django.db import migrations

UP_SQL = """
-- ============================================================
-- Invariant A: Double-entry balance check (deferred)
-- ============================================================
CREATE OR REPLACE FUNCTION verify_journal_entry_balance()
RETURNS TRIGGER AS $$
DECLARE
    v_debits  NUMERIC(18,2);
    v_credits NUMERIC(18,2);
BEGIN
    SELECT COALESCE(SUM(amount), 0) INTO v_debits
    FROM ledger_journaltransactionline
    WHERE journal_entry_id = NEW.id AND entry_type = 'DEBIT';

    SELECT COALESCE(SUM(amount), 0) INTO v_credits
    FROM ledger_journaltransactionline
    WHERE journal_entry_id = NEW.id AND entry_type = 'CREDIT';

    IF v_debits <> v_credits THEN
        RAISE EXCEPTION
            'Ledger Balance Mismatch: debits=% credits=%',
            v_debits, v_credits;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_enforce_ledger_balance ON ledger_journalentry;
CREATE CONSTRAINT TRIGGER trg_enforce_ledger_balance
    AFTER INSERT ON ledger_journalentry
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION verify_journal_entry_balance();

-- ============================================================
-- Invariant B: Immutable CERTIFIED journal entries
-- ============================================================
CREATE OR REPLACE FUNCTION protect_certified_ledger()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'CERTIFIED' THEN
        RAISE EXCEPTION
            'Immutability violation: certified journal_entries cannot be modified.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_block_ledger_mutation ON ledger_journalentry;
CREATE TRIGGER trg_block_ledger_mutation
    BEFORE UPDATE OR DELETE ON ledger_journalentry
    FOR EACH ROW
    EXECUTE FUNCTION protect_certified_ledger();

-- ============================================================
-- Invariant C: Guard cached balances
--   Applies to members.kapital_sosial_balance and
--   savings_membervoluntarydeposit.balance_available
--   Application sets SET LOCAL app.ledger_posting = 'true'
--   inside the transaction before performing the sync.
-- ============================================================
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


DOWN_SQL = """
DROP TRIGGER IF EXISTS trg_guard_hold_balance ON savings_membervoluntarydeposit;
DROP TRIGGER IF EXISTS trg_guard_voluntary_balance ON savings_membervoluntarydeposit;
DROP TRIGGER IF EXISTS trg_guard_member_capital_balance ON members_member;
DROP FUNCTION IF EXISTS guard_balance_update();

DROP TRIGGER IF EXISTS trg_block_ledger_mutation ON ledger_journalentry;
DROP FUNCTION IF EXISTS protect_certified_ledger();

DROP TRIGGER IF EXISTS trg_enforce_ledger_balance ON ledger_journalentry;
DROP FUNCTION IF EXISTS verify_journal_entry_balance();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("ledger", "0002_initial"),
        ("members", "0001_initial"),
        ("savings", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(UP_SQL, reverse_sql=DOWN_SQL),
    ]
