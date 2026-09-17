from django.db import transaction

from ledger.services import certify_journal_entry
from loans.models import Loan, LoanRepayment
from pipeline.registry import register


# ----------------------------------------------------------------
# Loan disbursement
# ----------------------------------------------------------------
@register("LOAN_DISBURSE", "on_certify")
@transaction.atomic
def on_loan_disbursed(actor, certifier_user):
    loan = Loan.objects.select_for_update().get(pk=actor.target_record_id)

    je = (
        certify_journal_entry(
            # Create the disbursement JE here (it was not created at DRAFT)
            # In this flow, we post only at certification, so we go through
            # post_journal_entry with auto_certify=True:
            journal_entry=loan.journal_entry,
            certified_by=certifier_user,
        )
        if loan.journal_entry
        else None
    )

    # If not yet created, create + certify in one step.
    if loan.journal_entry is None:
        from ledger.services import post_journal_entry
        from django.utils import timezone

        je = post_journal_entry(
            description=f"Loan disbursement – {loan.id}",
            lines=[
                ("1301", "DEBIT", loan.principal_original, loan.member),
                ("1001", "CREDIT", loan.principal_original),
            ],
            created_by=actor.maker,
            entry_date=timezone.localdate(),
            auto_certify=True,
            certified_by=certifier_user,
        )
        loan.journal_entry = je

    loan.status = Loan.Status.DISBURSED
    loan.disbursed_date = loan.journal_entry.entry_date
    loan.save(update_fields=["status", "disbursed_date", "journal_entry", "updated_at"])


@register("LOAN_DISBURSE", "on_reject")
@transaction.atomic
def on_loan_disbursement_rejected(actor, rejector_user, reason):
    loan = Loan.objects.select_for_update().get(pk=actor.target_record_id)
    # Leave as DRAFT; could optionally mark as CANCELLED.
    # (Loan model has no CANCELLED state to keep it minimal.)


# ----------------------------------------------------------------
# Loan repayment (manual or scheduled)
# ----------------------------------------------------------------
@register("LOAN_REPAY", "on_certify")
@transaction.atomic
def on_repayment_certified(actor, certifier_user):
    repayment = LoanRepayment.objects.select_for_update().get(pk=actor.target_record_id)
    loan = Loan.objects.select_for_update().get(pk=repayment.loan_id)

    certify_journal_entry(repayment.journal_entry, certifier_user)

    loan.principal_outstanding -= repayment.principal_paid
    if loan.principal_outstanding <= 0:
        loan.principal_outstanding = 0
        loan.status = Loan.Status.FULLY_REPAID
    loan.save(update_fields=["principal_outstanding", "status", "updated_at"])

    repayment.status = LoanRepayment.Status.COMPLETED
    repayment.save(update_fields=["status", "updated_at"])


@register("LOAN_REPAY", "on_reject")
@transaction.atomic
def on_repayment_rejected(actor, rejector_user, reason):
    repayment = LoanRepayment.objects.select_for_update().get(pk=actor.target_record_id)
    repayment.status = LoanRepayment.Status.REJECTED
    repayment.save(update_fields=["status", "updated_at"])
