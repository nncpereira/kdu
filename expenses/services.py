from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction

from accounting.models import Account
from core.services import round_money, today
from expenses.models import Expense
from ledger.services import post_journal_entry
from pipeline.services import create_pipeline

CASH = "1001"


@transaction.atomic
def record_expense(
    *,
    description: str,
    amount: Decimal,
    expense_account_code: str,
    payment_date=None,
    maker_user,
) -> Expense:
    """
    Record an operating expense. Posts a DRAFT JE:
        Dr Expense Account, Cr Cash
    """
    payment_date = payment_date or today()
    amount = round_money(Decimal(str(amount)))

    if amount <= 0:
        raise ValidationError("Amount must be positive.")
    if not description:
        raise ValidationError("Description is required.")

    # Validate the account exists and is an expense account
    acct = Account.objects.filter(
        account_code=expense_account_code, status="ACTIVE"
    ).first()
    if not acct:
        raise ValidationError(f"Account {expense_account_code} not found or inactive.")
    if acct.account_type != "EXPENSE":
        raise ValidationError(
            f"Account {expense_account_code} is not an expense account."
        )

    expense = Expense.objects.create(
        description=description,
        amount=amount,
        expense_account_code=expense_account_code,
        payment_date=payment_date,
        status=Expense.Status.PENDING_CHECK,
    )

    je = post_journal_entry(
        description=f"Expense: {description}",
        lines=[
            (expense_account_code, "DEBIT", amount),
            (CASH, "CREDIT", amount),
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
