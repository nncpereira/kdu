import uuid
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel, UUIDTimeStampedModel

class MemberSequence(models.Model):
    last_value = models.PositiveIntegerField(default=0)


def generate_membership_number() -> str:
    with transaction.atomic():
        seq, _ = MemberSequence.objects.select_for_update().get_or_create(id=1)
        seq.last_value += 1
        seq.save()
        return f"KDU-{seq.last_value:06d}"


class Member(TimeStampedModel):
    class Salutation(models.TextChoices):
        MR = "Mr", _("Mr.")
        MRS = "Mrs", _("Mrs.")
        MS = "Ms", _("Ms.")
        DR = "Dr", _("Dr.")
        PROF = "Prof", _("Prof.")
        REV = "Rev", _("Rev.")

    class Status(models.TextChoices):
        PENDING = "Pending", _("Pending")
        ACTIVE = "Active", _("Active")
        DORMANT = "Dormant", _("Dormant")
        SUSPENDED = "Suspended", _("Suspended")
        CLOSED = "Closed", _("Closed")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membership_number = models.CharField(max_length=20, unique=True, editable=False)

    # Optional link to Django auth user for self-service.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="member_profile",
        null=True,
        blank=True,
    )

    salutation = models.CharField(
        max_length=5, choices=Salutation.choices, default=Salutation.MR
    )
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    national_id = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    date_of_birth = models.DateField()

    aldeia = models.CharField(max_length=100, blank=True)
    suco = models.CharField(max_length=100, blank=True)
    posto = models.CharField(max_length=100, blank=True)
    municipio = models.CharField(max_length=100, blank=True)
    profession = models.CharField(max_length=100, blank=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    # Cached Kapital Sosial balance (maintained by ledger handler)
    kapital_sosial_balance = models.DecimalField(
        max_digits=18, decimal_places=2, default=0
    )

    date_joined = models.DateField(default=timezone.localdate)
    last_transaction_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["membership_number"]
        indexes = [models.Index(fields=["status", "last_transaction_at"])]

    def save(self, *args, **kwargs):
        if not self.membership_number:
            with transaction.atomic():
                self.membership_number = generate_membership_number()
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.membership_number

    @property
    def full_name(self):
        return " ".join(
            filter(None, [self.first_name, self.middle_name, self.last_name])
        )


class MemberOnboarding(UUIDTimeStampedModel):
    """
    Tracks the onboarding of a member, holding explicit references to the
    journal entry and pipeline actor so handlers know what to certify.
    """

    class Status(models.TextChoices):
        PENDING_CHECK = "PENDING_CHECK", "Pending Check"
        PENDING_CERTIFY = "PENDING_CERTIFY", "Pending Certify"
        COMPLETED = "COMPLETED", "Completed"
        REJECTED = "REJECTED", "Rejected"

    member = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="onboardings"
    )
    initial_capital_amount = models.DecimalField(max_digits=18, decimal_places=2)
    journal_entry = models.ForeignKey(
        "ledger.JournalEntry",
        on_delete=models.PROTECT,
        related_name="member_onboardings",
    )
    pipeline_actor = models.ForeignKey(
        "pipeline.TransactionPipelineActor",
        on_delete=models.PROTECT,
        related_name="member_onboardings",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING_CHECK
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Onboarding {self.member.membership_number} – {self.status}"


class MemberExitRequest(UUIDTimeStampedModel):
    """
    Tracks a member's exit request and the refund journal entry.
    """

    class Status(models.TextChoices):
        PENDING_CHECK = "PENDING_CHECK", "Pending Check"
        PENDING_CERTIFY = "PENDING_CERTIFY", "Pending Certify"
        COMPLETED = "COMPLETED", "Completed"
        REJECTED = "REJECTED", "Rejected"

    member = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="exit_requests"
    )
    refund_amount = models.DecimalField(max_digits=18, decimal_places=2)
    journal_entry = models.ForeignKey(
        "ledger.JournalEntry", on_delete=models.PROTECT, related_name="member_exits"
    )
    pipeline_actor = models.ForeignKey(
        "pipeline.TransactionPipelineActor",
        on_delete=models.PROTECT,
        related_name="member_exits",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING_CHECK
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Exit {self.member.membership_number} – {self.status}"
