from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from core.exceptions import DomainError
from core.services import round_money
from ledger.models import JournalEntry, JournalTransactionLine
from ledger.signals import journal_entry_certified


# ====================================================================
# Exceptions
# ====================================================================
class LedgerError(DomainError):
    """Base class for ledger service errors."""


class UnbalancedEntryError(LedgerError):
    pass


class AccountNotFoundError(LedgerError):
    pass


class ImmutableEntryError(LedgerError):
    pass


# ====================================================================
# Low-level helpers
# ====================================================================
def _check_account_exists(account_code: str):
    """Ensure the account exists and is ACTIVE in the Chart of Accounts."""
    from accounting.models import Account

    if not Account.objects.filter(account_code=account_code, status="ACTIVE").exists():
        raise AccountNotFoundError(f"Account {account_code} not found or inactive.")


def _normalise_lines(lines):
    """
    Accept lines as tuples (account_code, entry_type, amount[, member]) or
    dicts and return a normalised list of dicts.
    """
    normalised = []
    for line in lines:
        if isinstance(line, dict):
            d = dict(line)
        else:
            # tuple style
            if len(line) == 3:
                code, entry_type, amount = line
                member = None
            elif len(line) == 4:
                code, entry_type, amount, member = line
            else:
                raise ValidationError("Line tuple must have 3 or 4 elements.")
            d = {
                "account_code": code,
                "entry_type": entry_type,
                "amount": amount,
                "member": member,
            }

        d["amount"] = round_money(Decimal(str(d["amount"])))
        if d["amount"] <= 0:
            raise ValidationError("Line amounts must be positive.")
        if d["entry_type"] not in ("DEBIT", "CREDIT"):
            raise ValidationError("entry_type must be DEBIT or CREDIT.")

        _check_account_exists(d["account_code"])
        normalised.append(d)

    if len(normalised) < 2:
        raise ValidationError("A journal entry needs at least two lines.")
    return normalised


# ====================================================================
# Creation
# ====================================================================
@transaction.atomic
def post_journal_entry(
    *,
    description: str,
    lines: list,
    created_by,
    entry_date=None,
    auto_certify: bool = False,
    certified_by=None,
    original_journal_entry=None,
) -> JournalEntry:
    """
    Create a balanced journal entry with its lines.

    Args:
        description: Human-readable description.
        lines: List of (account_code, entry_type, amount[, member]) tuples or dicts.
        created_by: UserProfile creating the entry.
        entry_date: Defaults to today.
        auto_certify: If True, mark the entry CERTIFIED immediately (used by
                      trusted service flows like SHU payout after certification).
        certified_by: Required if auto_certify=True.
        original_journal_entry: Set for reversals.

    Returns:
        The created JournalEntry (with lines).

    Raises:
        UnbalancedEntryError if debits != credits.
        AccountNotFoundError if any account is missing.
    """
    entry_date = entry_date or timezone.localdate()
    normalised = _normalise_lines(lines)

    total_debits = sum(d["amount"] for d in normalised if d["entry_type"] == "DEBIT")
    total_credits = sum(d["amount"] for d in normalised if d["entry_type"] == "CREDIT")

    if total_debits != total_credits:
        raise UnbalancedEntryError(
            f"Debits ({total_debits}) != Credits ({total_credits})."
        )

    if auto_certify and certified_by is None:
        raise ValidationError("certified_by is required when auto_certify=True.")

    entry = JournalEntry.objects.create(
        entry_date=entry_date,
        description=description,
        status=(
            JournalEntry.Status.CERTIFIED if auto_certify else JournalEntry.Status.DRAFT
        ),
        created_by=created_by,
        certified_by=certified_by if auto_certify else None,
        original_journal_entry=original_journal_entry,
    )

    # Bulk-create lines; the DB trigger on INSERT will sync cached balances.
    JournalTransactionLine.objects.bulk_create(
        [
            JournalTransactionLine(
                journal_entry=entry,
                account_code=d["account_code"],
                entry_type=d["entry_type"],
                amount=d["amount"],
                member=d.get("member"),
            )
            for d in normalised
        ]
    )

    # If we're auto-certifying, emit the signal so cached balances update.
    if auto_certify:
        journal_entry_certified.send(
            sender=JournalEntry,
            journal_entry=entry,
            certified_by=certified_by,
        )

    return entry


# ====================================================================
# Certification (pipeline hook)
# ====================================================================
@transaction.atomic
def certify_journal_entry(entry: JournalEntry, certified_by) -> JournalEntry:
    """Move a DRAFT entry to CERTIFIED. Idempotent-safe."""
    if entry.status == JournalEntry.Status.CERTIFIED:
        return entry

    if not entry.is_balanced:
        raise UnbalancedEntryError("Cannot certify an unbalanced entry.")

    entry.status = JournalEntry.Status.CERTIFIED
    entry.certified_by = certified_by
    entry.save(update_fields=["status", "certified_by", "updated_at"])

    journal_entry_certified.send(
        sender=JournalEntry,
        journal_entry=entry,
        certified_by=certified_by,
    )
    return entry


# ====================================================================
# Reversal
# ====================================================================
@transaction.atomic
def reverse_journal_entry(
    original: JournalEntry,
    *,
    created_by,
    reason: str = "",
    auto_certify: bool = False,
    certified_by=None,
) -> JournalEntry:
    """
    Create a new entry that offsets the original.
    The original MUST already be CERTIFIED.
    """
    if original.status != JournalEntry.Status.CERTIFIED:
        raise ImmutableEntryError("Only certified entries can be reversed.")

    if original.reversals.exists():
        raise LedgerError("This entry has already been reversed.")

    # Swap debits <-> credits on every line.
    offset_lines = []
    for line in original.lines.all():
        opposite = "CREDIT" if line.entry_type == "DEBIT" else "DEBIT"
        offset_lines.append(
            {
                "account_code": line.account_code,
                "entry_type": opposite,
                "amount": line.amount,
                "member": line.member,
            }
        )

    return post_journal_entry(
        description=f"Reversal of {original.id}: {reason or original.description}",
        lines=offset_lines,
        created_by=created_by,
        auto_certify=auto_certify,
        certified_by=certified_by,
        original_journal_entry=original,
    )


# ====================================================================
# Balance queries
# ====================================================================
def account_net_balance(account_code: str, *, member=None, as_of=None) -> Decimal:
    """
    Net balance of an account using the normal convention:
        Asset / Expense       → DEBIT - CREDIT
        Liability / Equity / Revenue → CREDIT - DEBIT

    Args:
        account_code: CoA code.
        member: Optional Member to filter the sub-ledger.
        as_of: Optional date; defaults to all time.
    """
    from accounting.models import Account

    account = Account.objects.filter(account_code=account_code).first()
    if not account:
        raise AccountNotFoundError(f"Account {account_code} not found.")

    qs = JournalTransactionLine.objects.filter(
        account_code=account_code,
        journal_entry__status=JournalEntry.Status.CERTIFIED,
    )
    if member is not None:
        qs = qs.filter(member=member)
    if as_of is not None:
        qs = qs.filter(journal_entry__entry_date__lte=as_of)

    debits = qs.filter(entry_type="DEBIT").aggregate(t=models.Sum("amount"))[
        "t"
    ] or Decimal("0")
    credits = qs.filter(entry_type="CREDIT").aggregate(t=models.Sum("amount"))[
        "t"
    ] or Decimal("0")

    if account.account_type in ("ASSET", "EXPENSE"):
        return debits - credits
    return credits - debits


def account_balance_as_of(account_code: str, start, end, *, member=None) -> Decimal:
    """Net movement in an account between two dates (inclusive)."""
    from accounting.models import Account

    account = Account.objects.filter(account_code=account_code).first()
    if not account:
        raise AccountNotFoundError(f"Account {account_code} not found.")

    qs = JournalTransactionLine.objects.filter(
        account_code=account_code,
        journal_entry__status=JournalEntry.Status.CERTIFIED,
        journal_entry__entry_date__gte=start,
        journal_entry__entry_date__lte=end,
    )
    if member is not None:
        qs = qs.filter(member=member)

    debits = qs.filter(entry_type="DEBIT").aggregate(t=models.Sum("amount"))[
        "t"
    ] or Decimal("0")
    credits = qs.filter(entry_type="CREDIT").aggregate(t=models.Sum("amount"))[
        "t"
    ] or Decimal("0")

    if account.account_type in ("ASSET", "EXPENSE"):
        return debits - credits
    return credits - debits
