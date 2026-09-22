from django.db import models

from core.models import UUIDTimeStampedModel


class AuditLog(UUIDTimeStampedModel):
    """
    Records discrete system actions that aren't already captured by the
    domain models (JournalEntry, TransactionPipelineActor, etc.).

    Ledger movements are auditable via JournalEntry. This log captures
    the surrounding actions: logins, user management, config changes.
    """

    class Action(models.TextChoices):
        # Auth
        LOGIN_SUCCESS = "LOGIN_SUCCESS", "Login Success"
        LOGIN_FAILURE = "LOGIN_FAILURE", "Login Failure"
        LOGOUT = "LOGOUT", "Logout"

        # Staff user management
        USER_CREATED = "USER_CREATED", "User Created"
        USER_DISABLED = "USER_DISABLED", "User Disabled"
        USER_ENABLED = "USER_ENABLED", "User Enabled"
        USER_PASSWORD_RESET = "USER_PASSWORD_RESET", "User Password Reset"
        USER_UPDATED = "USER_UPDATED", "User Updated"

        # Member portal logins
        MEMBER_LOGIN_CREATED = "MEMBER_LOGIN_CREATED", "Member Login Created"
        MEMBER_LOGIN_RESET = "MEMBER_LOGIN_RESET", "Member Login Password Reset"

        # Governance
        CONFIG_PROPOSED = "CONFIG_PROPOSED", "Config Change Proposed"
        CONFIG_CERTIFIED = "CONFIG_CERTIFIED", "Config Change Certified"
        CONFIG_REJECTED = "CONFIG_REJECTED", "Config Change Rejected"

        # Domain
        MEMBER_EXIT_REQUESTED = "MEMBER_EXIT_REQUESTED", "Member Exit Requested"
        MEMBER_EXIT_COMPLETED = "MEMBER_EXIT_COMPLETED", "Member Exit Completed"
        REVERSAL_REQUESTED = "REVERSAL_REQUESTED", "Reversal Requested"
        REVERSAL_COMPLETED = "REVERSAL_COMPLETED", "Reversal Completed"

        OTHER = "OTHER", "Other"

    actor = models.ForeignKey(
        "users.UserProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
    )
    action = models.CharField(max_length=50, choices=Action.choices, db_index=True)
    target_type = models.CharField(max_length=50, blank=True, default="")
    target_id = models.UUIDField(null=True, blank=True)
    target_repr = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["actor", "-created_at"]),
        ]

    def __str__(self):
        who = self.actor.user.username if self.actor else "system"
        return f"{self.created_at:%Y-%m-%d %H:%M} · {who} · {self.action}"
