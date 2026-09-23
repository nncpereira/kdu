from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

# class UserProfileManager(models.Manager):
#     def get_by_natural_key(self, username):
#         return self.get(user__username=username)


class UserProfile(models.Model):
    """
    Extends Django's auth User with a role for the KDU pipeline.
    Every staff or member user has exactly one profile.
    """

    class Role(models.TextChoices):
        MAKER = "MAKER", _("Maker")
        CHECKER = "CHECKER", _("Checker")
        CERTIFIER = "CERTIFIER", _("Certifier")
        SUPERADMIN = "SUPERADMIN", _("Superadmin")
        MEMBER = "MEMBER", _("Member")
        BOARD = "BOARD", _("Board")  # read-only access
        AUDITOR = "AUDITOR", _("Auditor")  # read-only, PII-masked

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    must_change_password = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # objects = UserProfileManager()

    def natural_key(self):
        return (self.user.username,)

    natural_key.dependencies = ["auth.user"]

    class Meta:
        ordering = ["role", "user__username"]
        indexes = [models.Index(fields=["role"])]

    def __str__(self):
        return f"{self.user.username} [{self.role}]"

    # ---- Convenience helpers ------------------------------------------
    @property
    def is_maker(self):
        return self.role == self.Role.MAKER

    @property
    def is_checker(self):
        return self.role == self.Role.CHECKER

    @property
    def is_certifier(self):
        return self.role == self.Role.CERTIFIER

    @property
    def is_superadmin(self):
        return self.role == self.Role.SUPERADMIN

    @property
    def is_member(self):
        return self.role == self.Role.MEMBER

    @property
    def is_read_only(self):
        return self.role in {self.Role.BOARD, self.Role.AUDITOR}
