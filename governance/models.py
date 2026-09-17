from django.db import models
from core.models import UUIDTimeStampedModel


class GlobalConfig(UUIDTimeStampedModel):
    """
    Append-only configuration store.
    Each row represents a value that became effective on `effective_from`.
    A new row is written on every certified change.
    """

    parameter_key = models.CharField(max_length=100, db_index=True)
    parameter_value = models.JSONField()
    effective_from = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[("ACTIVE", "Active"), ("SUPERSEDED", "Superseded")],
        default="ACTIVE",
    )
    created_by = models.ForeignKey(
        "users.UserProfile", on_delete=models.PROTECT, related_name="config_changes"
    )

    class Meta:
        ordering = ["parameter_key", "-effective_from"]
        indexes = [models.Index(fields=["parameter_key", "effective_from"])]

    def __str__(self):
        return f"{self.parameter_key} from {self.effective_from}"


class GlobalConfigChange(UUIDTimeStampedModel):
    """
    Proposed change pending Maker-Checker-Certifier approval.
    On certification, a row is inserted into GlobalConfig.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_CHECK = "PENDING_CHECK", "Pending Check"
        PENDING_CERTIFY = "PENDING_CERTIFY", "Pending Certify"
        CERTIFIED = "CERTIFIED", "Certified"
        REJECTED = "REJECTED", "Rejected"

    parameter_key = models.CharField(max_length=100)
    proposed_value = models.JSONField()
    effective_from = models.DateField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    pipeline_actor = models.ForeignKey(
        "pipeline.TransactionPipelineActor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="config_changes",
    )
    created_by = models.ForeignKey(
        "users.UserProfile",
        on_delete=models.PROTECT,
        related_name="proposed_config_changes",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.parameter_key} -> {self.status}"
