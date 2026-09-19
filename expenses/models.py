import os
import uuid
from datetime import date
from django.db import models

# Create your models here.
from django.db import models
from core.models import UUIDTimeStampedModel


def receipt_upload_path(instance, filename):
    """
    Store receipts under media/receipts/YYYY/MM/<uuid>.<ext>.
    The uuid prevents filename collisions and avoids leaking
    the original filename in the URL.
    """
    ext = os.path.splitext(filename)[1].lower()
    today = date.today()
    return f"receipts/{today.year}/{today.month:02d}/{uuid.uuid4().hex}{ext}"


class Expense(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        PENDING_CHECK = "PENDING_CHECK", "Pending Check"
        PENDING_CERTIFY = "PENDING_CERTIFY", "Pending Certify"
        COMPLETED = "COMPLETED", "Completed"
        REJECTED = "REJECTED", "Rejected"
        REVERSED = "REVERSED", "Reversed"

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

    receipt = models.FileField(
        upload_to=receipt_upload_path,
        null=True,
        blank=True,
        help_text="Photo or PDF of the invoice/receipt. Max 5 MB.",
    )
