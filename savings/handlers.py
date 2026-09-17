from django.db import connection, transaction
from django.dispatch import receiver

from ledger.services import certify_journal_entry
from ledger.signals import journal_entry_certified
from pipeline.registry import register
from savings.models import MemberVoluntaryDeposit, Transaction


# ----------------------------------------------------------------
# Cache sync: 2101 lines update MemberVoluntaryDeposit.balance_available
# ----------------------------------------------------------------
@receiver(journal_entry_certified)
def _sync_voluntary_deposit(sender, journal_entry, certified_by, **kwargs):
    for line in journal_entry.lines.all():
        if line.account_code != "2101" or not line.member_id:
            continue

        with transaction.atomic():
            vd, _ = MemberVoluntaryDeposit.objects.select_for_update().get_or_create(
                member_id=line.member_id
            )
            delta = line.amount if line.entry_type == "CREDIT" else -line.amount
            vd.balance_available += delta
            # with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute("SET LOCAL app.ledger_posting = 'true'")
            vd.save(update_fields=["balance_available", "updated_at"])


# ----------------------------------------------------------------
# Deposit pipeline completion (unchanged – cache handled by signal)
# ----------------------------------------------------------------
@register("DEPOSIT", "on_certify")
@transaction.atomic
def on_deposit_certified(actor, certifier_user):
    txn = Transaction.objects.select_for_update().get(pk=actor.target_record_id)
    if txn.journal_entry is None:
        raise ValueError("Deposit transaction has no journal entry")
    certify_journal_entry(txn.journal_entry, certifier_user)
    txn.status = Transaction.Status.COMPLETED
    txn.save(update_fields=["status", "updated_at"])


@register("DEPOSIT", "on_reject")
@transaction.atomic
def on_deposit_rejected(actor, rejector_user, reason):
    txn = Transaction.objects.select_for_update().get(pk=actor.target_record_id)
    txn.status = Transaction.Status.REJECTED
    txn.save(update_fields=["status", "updated_at"])


# ----------------------------------------------------------------
# Withdrawal pipeline completion
# balance_available is adjusted by the signal receiver above.
# Here we only release the escrow hold and mark the txn complete.
# ----------------------------------------------------------------
@register("WITHDRAWAL", "on_certify")
@transaction.atomic
def on_withdrawal_certified(actor, certifier_user):
    txn = Transaction.objects.select_for_update().get(pk=actor.target_record_id)

    # 1. Certify the JE → signal fires → balance_available -= amount
    if txn.journal_entry is None:
        raise ValueError("Withdrawal transaction has no journal entry")
    certify_journal_entry(txn.journal_entry, certifier_user)

    # 2. Release the escrow hold. balance_available is reduced by the ledger
    # sync handler (see ledger/signals.py – on entry certified).
    vd = MemberVoluntaryDeposit.objects.select_for_update().get(member=txn.member)
    vd.balance_held_pipeline -= txn.requested_amount

    with connection.cursor() as cur:
        cur.execute("SET LOCAL app.ledger_posting = 'true'")
    vd.save(update_fields=["balance_held_pipeline", "updated_at"])

    txn.status = Transaction.Status.COMPLETED
    txn.save(update_fields=["status", "updated_at"])


@register("WITHDRAWAL", "on_reject")
@transaction.atomic
def on_withdrawal_rejected(actor, rejector_user, reason):
    txn = Transaction.objects.select_for_update().get(pk=actor.target_record_id)

    # Release the escrow hold
    vd = MemberVoluntaryDeposit.objects.select_for_update().get(member=txn.member)
    vd.balance_held_pipeline -= txn.requested_amount
    with connection.cursor() as cur:
        cur.execute("SET LOCAL app.ledger_posting = 'true'")
    vd.save(update_fields=["balance_held_pipeline", "updated_at"])

    txn.status = Transaction.Status.REJECTED
    txn.save(update_fields=["status", "updated_at"])
