from django.db import models

from core.models import UUIDTimeStampedModel


class Loan(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        DISBURSED = "DISBURSED", "Disbursed"
        FULLY_REPAID = "FULLY_REPAID", "Fully Repaid"
        WRITTEN_OFF = "WRITTEN_OFF", "Written Off"

    member = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="loans"
    )
    principal_original = models.DecimalField(max_digits=18, decimal_places=2)
    principal_outstanding = models.DecimalField(max_digits=18, decimal_places=2)
    monthly_rate = models.DecimalField(max_digits=6, decimal_places=4)  # e.g. 0.0150
    term_months = models.PositiveIntegerField()
    purpose = models.CharField(max_length=255, blank=True)
    disbursed_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    pipeline_actor = models.ForeignKey(
        "pipeline.TransactionPipelineActor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="loans",
    )
    journal_entry = models.ForeignKey(
        "ledger.JournalEntry",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="loans_disbursed",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Loan {self.id} – {self.member.membership_number} ({self.status})"


class LoanRepayment(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        PENDING_CHECK = "PENDING_CHECK", "Pending Check"
        PENDING_CERTIFY = "PENDING_CERTIFY", "Pending Certify"
        COMPLETED = "COMPLETED", "Completed"
        REJECTED = "REJECTED", "Rejected"
        REVERSED = "REVERSED", "Reversed"

    loan = models.ForeignKey(Loan, on_delete=models.PROTECT, related_name="repayments")
    principal_paid = models.DecimalField(max_digits=18, decimal_places=2)
    interest_paid = models.DecimalField(max_digits=18, decimal_places=2)
    payment_date = models.DateField()
    mode = models.CharField(
        max_length=20,
        choices=[("MANUAL", "Manual"), ("SCHEDULED", "Scheduled")],
        default="MANUAL",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING_CHECK
    )
    pipeline_actor = models.ForeignKey(
        "pipeline.TransactionPipelineActor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="loan_repayments",
    )
    journal_entry = models.ForeignKey(
        "ledger.JournalEntry",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="loan_repayments",
    )

    class Meta:
        ordering = ["-payment_date", "-created_at"]

    def __str__(self):
        return f"Repayment {self.id} – {self.loan_id}"
