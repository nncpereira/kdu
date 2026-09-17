from django.db import models
from core.models import UUIDTimeStampedModel


class MemberVoluntaryDeposit(UUIDTimeStampedModel):
    """Cached balance for a member's voluntary deposit account.
    Real balance is derived from the ledger; this table is maintained
    by ledger certification handlers for fast lookups.
    """

    member = models.OneToOneField(
        "members.Member",
        on_delete=models.PROTECT,
        related_name="voluntary_deposit",
    )
    balance_available = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    balance_held_pipeline = models.DecimalField(
        max_digits=18, decimal_places=2, default=0
    )

    class Meta:
        verbose_name = "Member Voluntary Deposit"

    def __str__(self):
        return f"{self.member.membership_number} – avail {self.balance_available}"


class Transaction(UUIDTimeStampedModel):
    class Type(models.TextChoices):
        DEPOSIT = "DEPOSIT", "Deposit"
        WITHDRAWAL = "WITHDRAWAL", "Withdrawal"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_CHECK = "PENDING_CHECK", "Pending Check"
        PENDING_CERTIFY = "PENDING_CERTIFY", "Pending Certify"
        COMPLETED = "COMPLETED", "Completed"
        REJECTED = "REJECTED", "Rejected"

    member = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="savings_transactions"
    )
    transaction_type = models.CharField(max_length=20, choices=Type.choices)
    requested_amount = models.DecimalField(max_digits=18, decimal_places=2)
    obligatory_portion = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    voluntary_portion = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    pipeline_actor = models.ForeignKey(
        "pipeline.TransactionPipelineActor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="savings_transactions",
    )
    journal_entry = models.ForeignKey(
        "ledger.JournalEntry",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="savings_transactions",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["member", "transaction_type", "status"]),
        ]

    def __str__(self):
        return f"{self.transaction_type} {self.requested_amount} – {self.member.membership_number}"
