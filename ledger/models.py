import uuid
from django.db import models

from core.models import UUIDTimeStampedModel


class JournalEntry(UUIDTimeStampedModel):
    """
    A single double-entry transaction. Immutable once CERTIFIED.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        CERTIFIED = "CERTIFIED", "Certified"

    entry_date = models.DateField(db_index=True)
    description = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    original_journal_entry = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reversals",
        help_text="If this entry is a reversal, points to the original.",
    )
    created_by = models.ForeignKey(
        "users.UserProfile",
        on_delete=models.PROTECT,
        related_name="journal_entries_created",
    )
    certified_by = models.ForeignKey(
        "users.UserProfile",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="journal_entries_certified",
    )

    class Meta:
        ordering = ["-entry_date", "-created_at"]
        indexes = [
            models.Index(fields=["status", "entry_date"]),
            models.Index(fields=["original_journal_entry"]),
        ]

    def __str__(self):
        return f"JE-{self.id} {self.entry_date} [{self.status}]"

    # ---- Domain helpers -------------------------------------------------
    @property
    def total_debits(self):
        return (
            self.lines.filter(
                entry_type=JournalTransactionLine.EntryType.DEBIT
            ).aggregate(total=models.Sum("amount"))["total"]
            or 0
        )

    @property
    def total_credits(self):
        return (
            self.lines.filter(
                entry_type=JournalTransactionLine.EntryType.CREDIT
            ).aggregate(total=models.Sum("amount"))["total"]
            or 0
        )

    @property
    def is_balanced(self):
        return self.total_debits == self.total_credits


class JournalTransactionLine(models.Model):
    """
    A single leg of a journal entry. Each JE must have >= 2 lines,
    and total debits must equal total credits.
    """

    class EntryType(models.TextChoices):
        DEBIT = "DEBIT", "Debit"
        CREDIT = "CREDIT", "Credit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    account_code = models.CharField(max_length=20, db_index=True)
    member = models.ForeignKey(
        "members.Member",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="journal_lines",
    )
    entry_type = models.CharField(max_length=6, choices=EntryType.choices)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["journal_entry_id", "created_at"]
        indexes = [
            models.Index(fields=["account_code", "entry_type"]),
            models.Index(fields=["member", "account_code"]),
        ]

    def __str__(self):
        return f"{self.entry_type} {self.account_code} {self.amount}"


class ReversalRequest(UUIDTimeStampedModel):
    """
    Tracks a request to reverse a certified journal entry.
    The original entry is never modified; an offsetting entry is posted
    once the pipeline completes.
    """

    class Status(models.TextChoices):
        PENDING_CHECK = "PENDING_CHECK", "Pending Check"
        PENDING_CERTIFY = "PENDING_CERTIFY", "Pending Certify"
        COMPLETED = "COMPLETED", "Completed"
        REJECTED = "REJECTED", "Rejected"

    class SourceType(models.TextChoices):
        SAVINGS_TRANSACTION = "SAVINGS_TRANSACTION", "Savings Transaction"
        LOAN_REPAYMENT = "LOAN_REPAYMENT", "Loan Repayment"
        EXPENSE = "EXPENSE", "Expense"
        OTHER = "OTHER", "Other"

    original_journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.PROTECT,
        related_name="reversal_requests",
    )
    reversal_journal_entry = models.ForeignKey(
        JournalEntry,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reversed_from",
    )
    source_type = models.CharField(max_length=30, choices=SourceType.choices)
    source_id = models.UUIDField(null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING_CHECK
    )
    pipeline_actor = models.ForeignKey(
        "pipeline.TransactionPipelineActor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reversal_requests",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["original_journal_entry"]),
        ]

    def __str__(self):
        return f"Reversal of {self.original_journal_entry_id} [{self.status}]"
