import os
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction

from accounting.models import Account
from core.services import round_money, today
from expenses.models import Expense
from ledger.services import post_journal_entry
from pipeline.services import create_pipeline

CASH = "1001"

MAX_RECEIPT_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_RECEIPT_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


def _validate_receipt(receipt_file):
    """Raise ValidationError if the receipt violates size or type limits."""
    if receipt_file is None:
        return

    if receipt_file.size > MAX_RECEIPT_SIZE:
        raise ValidationError(
            f"Receipt is too large ({receipt_file.size} bytes). "
            f"Maximum allowed is 5 MB."
        )

    ext = os.path.splitext(receipt_file.name)[1].lower()
    if ext not in ALLOWED_RECEIPT_EXTS:
        raise ValidationError(
            f"Unsupported receipt format: {ext or 'unknown'}. "
            f"Allowed: {', '.join(sorted(ALLOWED_RECEIPT_EXTS))}."
        )


@transaction.atomic
def record_expense(
    *,
    description: str,
    amount,
    expense_account_code: str,
    payment_date=None,
    receipt=None,
    maker_user,
) -> Expense:
    """
    Record an operating expense. Optionally attaches a receipt file.
    Posts a DRAFT JE: Dr Expense Account, Cr Cash.
    """
    from accounting.models import Account
    from core.services import round_money, today

    payment_date = payment_date or today()
    amount = round_money(Decimal(str(amount)))

    if amount <= 0:
        raise ValidationError("Amount must be positive.")
    if not description:
        raise ValidationError("Description is required.")

    acct = Account.objects.filter(
        account_code=expense_account_code, status="ACTIVE"
    ).first()
    if not acct:
        raise ValidationError(f"Account {expense_account_code} not found or inactive.")
    if acct.account_type != "EXPENSE":
        raise ValidationError(
            f"Account {expense_account_code} is not an expense account."
        )

    _validate_receipt(receipt)

    expense = Expense.objects.create(
        description=description,
        amount=amount,
        expense_account_code=expense_account_code,
        payment_date=payment_date,
        receipt=receipt,
        status=Expense.Status.PENDING_CHECK,
    )

    je = post_journal_entry(
        description=f"Expense: {description}",
        lines=[
            (expense_account_code, "DEBIT", amount),
            ("1001", "CREDIT", amount),
        ],
        created_by=maker_user,
        entry_date=payment_date,
    )
    expense.journal_entry = je
    expense.save(update_fields=["journal_entry"])

    actor = create_pipeline(
        transaction_type="EXPENSE",
        target_record_id=expense.id,
        maker_user=maker_user,
    )
    expense.pipeline_actor = actor
    expense.save(update_fields=["pipeline_actor"])
    return expense
