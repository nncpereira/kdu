from pipeline.summaries import register_summary


@register_summary("EXPENSE")
def _expense(expense_id):
    from expenses.models import Expense

    e = Expense.objects.get(id=expense_id)
    return {
        "label": f"{e.description} — ${e.amount} (acct {e.expense_account_code})",
        "kind": "EXPENSE",
        "amount": str(e.amount),
        "expense_account_code": e.expense_account_code,
        "description": e.description,
        "has_receipt": bool(e.receipt),
        "receipt_url": e.receipt.url if e.receipt else None,
    }
