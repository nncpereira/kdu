from datetime import datetime

from django.db import connection, transaction
from django.dispatch import receiver
from django.utils import timezone

from ledger.services import certify_journal_entry
from ledger.signals import journal_entry_certified
from members.models import Member, MemberExitRequest, MemberOnboarding
from members.services import provision_member_user
from pipeline.registry import register


# ----------------------------------------------------------------
# Cache sync: any certified JE that touches 3101 updates the member cache
# ----------------------------------------------------------------
@receiver(journal_entry_certified)
def _sync_kapital_sosial(sender, journal_entry, certified_by, **kwargs):
    for line in journal_entry.lines.all():
        if line.account_code != "3101" or not line.member_id:
            continue

        with transaction.atomic():
            member = Member.objects.select_for_update().get(pk=line.member_id)
            delta = line.amount if line.entry_type == "CREDIT" else -line.amount
            member.kapital_sosial_balance += delta
            member.last_transaction_at = timezone.make_aware(
                datetime.combine(journal_entry.entry_date, datetime.min.time())
            )

        # Bypass the guard trigger for this controlled update.
        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute("SET LOCAL app.ledger_posting = 'true'")
            member.save(
                update_fields=[
                    "kapital_sosial_balance",
                    "last_transaction_at",
                    "updated_at",
                ]
            )


# ----------------------------------------------------------------
# Onboarding pipeline completion
# ----------------------------------------------------------------
@register("MEMBER_ONBOARD", "on_certify")
@transaction.atomic
def on_onboarding_certified(actor, certifier_user):
    onboarding = MemberOnboarding.objects.select_for_update().get(
        pk=actor.target_record_id  # ← was: pipeline_actor=actor
    )
    certify_journal_entry(onboarding.journal_entry, certifier_user)

    member = Member.objects.select_for_update().get(pk=onboarding.member_id)
    if member.kapital_sosial_balance >= 50:
        member.status = Member.Status.ACTIVE
        member.save(update_fields=["status", "updated_at"])
        provision_member_user(member)

    onboarding.status = MemberOnboarding.Status.COMPLETED
    onboarding.save(update_fields=["status", "updated_at"])


@register("MEMBER_ONBOARD", "on_reject")
@transaction.atomic
def on_onboarding_rejected(actor, rejector_user, reason):
    onboarding = MemberOnboarding.objects.select_for_update().get(
        pk=actor.target_record_id  # ← was: pipeline_actor=actor
    )
    onboarding.status = MemberOnboarding.Status.REJECTED
    onboarding.save(update_fields=["status", "updated_at"])


# ----------------------------------------------------------------
# Exit pipeline completion
# ----------------------------------------------------------------
@register("MEMBER_EXIT", "on_certify")
@transaction.atomic
def on_exit_certified(actor, certifier_user):
    exit_req = MemberExitRequest.objects.select_for_update().get(
        pk=actor.target_record_id  # ← was: pipeline_actor=actor
    )
    certify_journal_entry(exit_req.journal_entry, certifier_user)

    member = Member.objects.select_for_update().get(pk=exit_req.member_id)
    member.status = Member.Status.CLOSED
    member.save(update_fields=["status", "updated_at"])

    exit_req.status = MemberExitRequest.Status.COMPLETED
    exit_req.save(update_fields=["status", "updated_at"])

    if member.user_id:
        member.user.is_active = False
        member.user.save(update_fields=["is_active"])


@register("MEMBER_EXIT", "on_reject")
@transaction.atomic
def on_exit_rejected(actor, rejector_user, reason):
    exit_req = MemberExitRequest.objects.select_for_update().get(
        pk=actor.target_record_id  # ← was: pipeline_actor=actor
    )
    exit_req.status = MemberExitRequest.Status.REJECTED
    exit_req.save(update_fields=["status", "updated_at"])
