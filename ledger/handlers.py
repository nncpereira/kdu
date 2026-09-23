from django.db import transaction

from ledger.models import ReversalRequest
from ledger.services import reverse_journal_entry
from pipeline.registry import register


# ====================================================================
# Reversal completion
# ====================================================================
@register("JOURNAL_REVERSAL", "on_certify")
@transaction.atomic
def on_reversal_certified(actor, certifier_user):
    req = ReversalRequest.objects.select_for_update().get(pipeline_actor=actor)

    reversal_entry = reverse_journal_entry(
        req.original_journal_entry,
        created_by=certifier_user,
        reason=req.reason,
        auto_certify=True,
        certified_by=certifier_user,
    )

    req.reversal_journal_entry = reversal_entry
    req.status = ReversalRequest.Status.COMPLETED
    req.save(update_fields=["reversal_journal_entry", "status", "updated_at"])

    _mark_source_reversed(req)


@register("JOURNAL_REVERSAL", "on_reject")
@transaction.atomic
def on_reversal_rejected(actor, rejector_user, reason):
    req = ReversalRequest.objects.select_for_update().get(pipeline_actor=actor)
    req.status = ReversalRequest.Status.REJECTED
    req.save(update_fields=["status", "updated_at"])


def _mark_source_reversed(req: ReversalRequest):
    """Flip the domain record's status to REVERSED."""
    if not req.source_id:
        return

    if req.source_type == ReversalRequest.SourceType.SAVINGS_TRANSACTION:
        from savings.models import Transaction

        Transaction.objects.filter(id=req.source_id).update(status="REVERSED")

    elif req.source_type == ReversalRequest.SourceType.LOAN_REPAYMENT:
        from loans.models import LoanRepayment

        LoanRepayment.objects.filter(id=req.source_id).update(status="REVERSED")

    elif req.source_type == ReversalRequest.SourceType.EXPENSE:
        from expenses.models import Expense

        Expense.objects.filter(id=req.source_id).update(status="REVERSED")
