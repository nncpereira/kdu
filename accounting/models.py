from django.db import models

from core.models import UUIDTimeStampedModel


class Account(UUIDTimeStampedModel):
    """
    Chart of Accounts entry. Referenced by account_code throughout
    the ledger and services.
    """

    class Type(models.TextChoices):
        ASSET = "ASSET", "Asset"
        LIABILITY = "LIABILITY", "Liability"
        EQUITY = "EQUITY", "Equity"
        REVENUE = "REVENUE", "Revenue"
        EXPENSE = "EXPENSE", "Expense"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    account_code = models.CharField(max_length=20, unique=True)
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=Type.choices)
    parent_account_code = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )

    class Meta:
        ordering = ["account_code"]
        indexes = [models.Index(fields=["account_type", "status"])]

    def __str__(self):
        return f"{self.account_code} – {self.account_name}"
