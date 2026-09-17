from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from core.exceptions import InsufficientBalanceError
from core.services import round_money, today
from governance.services import get_active_value
from ledger.services import post_journal_entry
from pipeline.services import create_pipeline
from savings.models import MemberVoluntaryDeposit, Transaction

CASH = "1001"
KAPITAL_SOSIAL = "3101"
VOLUNTARY_DEPOSIT = "2101"


# ====================================================================
# Helpers
# ====================================================================
def _remaining_obligatory_cap(member, as_of) -> Decimal:
    """
    How much obligatory savings can still be charged this calendar month.
    Cap comes from governance config.
    """
    cap = get_active_value("obligatory_savings_monthly_cap", as_of=as_of)
    cap = Decimal(str(cap)) if cap is not None else Decimal(0)

    first_of_month = as_of.replace(day=1)
    contributed = (
        Transaction.objects.filter(
            member=member,
            transaction_type=Transaction.Type.DEPOSIT,
            status=Transaction.Status.COMPLETED,
            created_at__date__gte=first_of_month,
            created_at__date__lte=as_of,
        ).aggregate(t=Sum("obligatory_portion"))["t"]
        or 0
    )
    return max(cap - contributed, 0)


def _ensure_voluntary_row(member) -> MemberVoluntaryDeposit:
    vd, _ = MemberVoluntaryDeposit.objects.get_or_create(member=member)
    return vd


# ====================================================================
# Deposit
# ====================================================================
@transaction.atomic
def deposit(*, member, amount, maker_user, entry_date=None) -> Transaction:
    """
    Member cash deposit. Splits the first part of the month's deposit into
    obligatory savings (Kapital Sosial, equity) up to the monthly cap;
    the remainder goes to voluntary deposits (liability).
    """
    entry_date = entry_date or today()
    amount = round_money(Decimal(str(amount)))

    if amount <= 0:
        raise ValidationError("Deposit amount must be positive.")
    if member.status != "Active":
        raise ValidationError("Member is not active.")

    cap_remaining = _remaining_obligatory_cap(member, entry_date)
    obligatory = min(amount, cap_remaining)
    voluntary = amount - obligatory

    # 1. Create the DRAFT transaction record
    txn = Transaction.objects.create(
        member=member,
        transaction_type=Transaction.Type.DEPOSIT,
        requested_amount=amount,
        obligatory_portion=obligatory,
        voluntary_portion=voluntary,
        status=Transaction.Status.PENDING_CHECK,
    )

    # 2. Post a DRAFT journal entry (no balance side effects yet)
    lines: list[tuple[str, str, Decimal] | tuple[str, str, Decimal, object]] = [
        (CASH, "DEBIT", amount)
    ]
    if obligatory > 0:
        lines.append((KAPITAL_SOSIAL, "CREDIT", obligatory, member))
    if voluntary > 0:
        lines.append((VOLUNTARY_DEPOSIT, "CREDIT", voluntary, member))

    je = post_journal_entry(
        description=f"Deposit for {member.membership_number}",
        lines=lines,
        created_by=maker_user,
        entry_date=entry_date,
    )
    Transaction.objects.filter(pk=txn.pk).update(journal_entry=je)
    txn.journal_entry_id = je.id

    # 3. Create the Maker-Checker-Certifier pipeline
    actor = create_pipeline(
        transaction_type="DEPOSIT",
        target_record_id=txn.id,
        maker_user=maker_user,
    )
    txn.pipeline_actor = actor
    txn.save(update_fields=["pipeline_actor"])

    return txn


# ====================================================================
# Withdrawal
# ====================================================================
@transaction.atomic
def withdraw(*, member, amount, maker_user, entry_date=None) -> Transaction:
    """
    Withdraw from voluntary deposits only. Obligatory capital stays locked.
    Places an escrow hold to prevent concurrent withdrawals.
    """
    from django.db import connection

    entry_date = entry_date or today()
    amount = round_money(Decimal(str(amount)))

    if amount <= 0:
        raise ValidationError("Withdrawal amount must be positive.")
    if member.status != "Active":
        raise ValidationError("Member is not active.")

    # Lock the row, then compute available
    vd = _ensure_voluntary_row(member)
    vd = MemberVoluntaryDeposit.objects.select_for_update().get(pk=vd.pk)
    available = vd.balance_available - vd.balance_held_pipeline

    if available < amount:
        raise InsufficientBalanceError(
            f"Insufficient voluntary funds: available {available}, requested {amount}."
        )

    # Place the escrow hold
    vd.balance_held_pipeline += amount
    with connection.cursor() as cur:
        cur.execute("SET LOCAL app.ledger_posting = 'true'")
    vd.save(update_fields=["balance_held_pipeline", "updated_at"])

    # DRAFT transaction
    txn = Transaction.objects.create(
        member=member,
        transaction_type=Transaction.Type.WITHDRAWAL,
        requested_amount=amount,
        obligatory_portion=Decimal("0"),
        voluntary_portion=amount,
        status=Transaction.Status.PENDING_CHECK,
    )

    # DRAFT journal entry
    je = post_journal_entry(
        description=f"Withdrawal for {member.membership_number}",
        lines=[
            (VOLUNTARY_DEPOSIT, "DEBIT", amount, member),
            (CASH, "CREDIT", amount),
        ],
        created_by=maker_user,
        entry_date=entry_date,
    )
    Transaction.objects.filter(pk=txn.pk).update(journal_entry=je)
    txn.journal_entry_id = je.id

    actor = create_pipeline(
        transaction_type="WITHDRAWAL",
        target_record_id=txn.id,
        maker_user=maker_user,
    )
    txn.pipeline_actor = actor
    txn.save(update_fields=["pipeline_actor"])

    return txn
