from django.db import models

# Create your models here.
from django.db import models
from core.models import UUIDTimeStampedModel


class Expense(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        PENDING_CHECK = "PENDING_CHECK", "Pending Check"
        PENDING_CERTIFY = "PENDING_CERTIFY", "Pending Certify"
        COMPLETED = "COMPLETED", "Completed"
        REJECTED = "REJECTED", "Rejected"

    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    expense_account_code = models.CharField(max_length=20)  # references CoA
    payment_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING_CHECK
    )
    pipeline_actor = models.ForeignKey(
        "pipeline.TransactionPipelineActor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="expenses",
    )
    journal_entry = models.ForeignKey(
        "ledger.JournalEntry",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="expenses",
    )

    class Meta:
        ordering = ["-payment_date", "-created_at"]
        indexes = [
            models.Index(fields=["expense_account_code", "payment_date"]),
        ]

    def __str__(self):
        return f"Expense {self.id} – {self.amount} ({self.expense_account_code})"
