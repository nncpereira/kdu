from django.db import transaction

from expenses.models import Expense
from ledger.services import certify_journal_entry
from pipeline.registry import register


@register("EXPENSE", "on_certify")
@transaction.atomic
def on_expense_certified(actor, certifier_user):
    expense = Expense.objects.select_for_update().get(pk=actor.target_record_id)
    certify_journal_entry(expense.journal_entry, certifier_user)
    expense.status = Expense.Status.COMPLETED
    expense.save(update_fields=["status", "updated_at"])


@register("EXPENSE", "on_reject")
@transaction.atomic
def on_expense_rejected(actor, rejector_user, reason):
    expense = Expense.objects.select_for_update().get(pk=actor.target_record_id)
    expense.status = Expense.Status.REJECTED
    expense.save(update_fields=["status", "updated_at"])
