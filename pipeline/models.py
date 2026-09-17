from django.db import models

from core.models import UUIDTimeStampedModel


class TransactionPipelineActor(UUIDTimeStampedModel):
    """
    Universal tracking row for the Maker-Checker-Certifier workflow.
    One row per financial mutation. Domain handlers register via
    pipeline.registry to execute on check / certify / reject.
    """

    class Status(models.TextChoices):
        PENDING_CHECK = "PENDING_CHECK", "Pending Check"
        PENDING_CERTIFY = "PENDING_CERTIFY", "Pending Certify"
        COMPLETED = "COMPLETED", "Completed"
        REJECTED = "REJECTED", "Rejected"

    transaction_type = models.CharField(max_length=50, db_index=True)
    target_record_id = models.UUIDField(db_index=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING_CHECK
    )
    maker = models.ForeignKey(
        "users.UserProfile", null=True, blank=True,
        on_delete=models.PROTECT,
        related_name="made_pipeline_actors",
    )
    checker = models.ForeignKey(
        "users.UserProfile", 
        on_delete=models.PROTECT,
        related_name="checked_pipeline_actors",
        null=True,
        blank=True,
    )
    certifier = models.ForeignKey(
        "users.UserProfile",
        on_delete=models.PROTECT,
        related_name="certified_pipeline_actors",
        null=True,
        blank=True,
    )
    rejection_reason = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status", "transaction_type"]),
            models.Index(fields=["transaction_type", "target_record_id"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(checker__isnull=True)
                | ~models.Q(maker=models.F("checker")),
                name="ck_pipeline_maker_ne_checker",
            ),
            models.CheckConstraint(
                check=models.Q(certifier__isnull=True)
                | ~models.Q(maker=models.F("certifier")),
                name="ck_pipeline_maker_ne_certifier",
            ),
            models.CheckConstraint(
                check=models.Q(certifier__isnull=True)
                | models.Q(checker__isnull=True)
                | ~models.Q(checker=models.F("certifier")),
                name="ck_pipeline_checker_ne_certifier",
            ),
        ]

    def __str__(self):
        return f"{self.transaction_type} [{self.status}] ({self.target_record_id})"
