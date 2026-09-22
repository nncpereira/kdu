"""
Notification aggregation for the sidebar bell.

Returns role-aware, actionable items — things the current user can
or should do something about.
"""

from datetime import timedelta

from django.utils import timezone

from pipeline.models import TransactionPipelineActor
from pipeline.summaries import get_summary

# Pipeline transaction types that are user-facing (skip system-generated ones).
USER_FACING_TYPES = {
    "DEPOSIT",
    "WITHDRAWAL",
    "LOAN_DISBURSE",
    "LOAN_REPAY",
    "EXPENSE",
    "MEMBER_ONBOARD",
    "MEMBER_EXIT",
    "SHU_CALCULATE",
    "JOURNAL_REVERSAL",
}


def _actor_to_item(actor: TransactionPipelineActor) -> dict:
    """Turn a pipeline actor into a notification-shaped dict."""
    summary = get_summary(actor.transaction_type, actor.target_record_id)
    return {
        "id": str(actor.id),
        "kind": "PIPELINE",
        "transaction_type": actor.transaction_type,
        "status": actor.status,
        "label": summary.get("label") if summary else actor.transaction_type,
        "maker_username": (actor.maker.user.username if actor.maker else None),
        "updated_at": actor.updated_at.isoformat(),
        "link": "/pipeline",
    }


def get_notifications_for(profile) -> list[dict]:
    """
    Return a list of notification dicts for the given UserProfile.

    Each item has:
      id, kind, label, status, link, updated_at, ...
    Sorted by updated_at desc.
    """
    role = profile.role
    items: list[dict] = []

    # ---- Pipeline queues (Checker / Certifier / Superadmin) --------
    if role in {"CHECKER", "SUPERADMIN"}:
        pending_check = (
            TransactionPipelineActor.objects.filter(
                status=TransactionPipelineActor.Status.PENDING_CHECK,
                transaction_type__in=USER_FACING_TYPES,
            )
            .select_related("maker__user")
            .order_by("-updated_at")[:50]
        )
        for actor in pending_check:
            item = _actor_to_item(actor)
            item["queue"] = "PENDING_CHECK"
            item["action"] = "Approve or reject"
            items.append(item)

    if role in {"CERTIFIER", "SUPERADMIN"}:
        pending_certify = (
            TransactionPipelineActor.objects.filter(
                status=TransactionPipelineActor.Status.PENDING_CERTIFY,
                transaction_type__in=USER_FACING_TYPES,
            )
            .select_related("maker__user")
            .order_by("-updated_at")[:50]
        )
        for actor in pending_certify:
            item = _actor_to_item(actor)
            item["queue"] = "PENDING_CERTIFY"
            item["action"] = "Certify or reject"
            items.append(item)

    # ---- Maker's rejected submissions (last 7 days) ----------------
    if role in {"MAKER", "SUPERADMIN"}:
        cutoff = timezone.now() - timedelta(days=7)
        rejected = TransactionPipelineActor.objects.filter(
            maker=profile,
            status=TransactionPipelineActor.Status.REJECTED,
            updated_at__gte=cutoff,
            transaction_type__in=USER_FACING_TYPES,
        ).order_by("-updated_at")[:20]
        for actor in rejected:
            item = _actor_to_item(actor)
            item["queue"] = "REJECTED"
            item["action"] = "Rejected"
            item["reason"] = actor.rejection_reason
            items.append(item)

    # ---- Deduplicate and sort --------------------------------------
    # A Superadmin might see the same actor twice if they made and can
    # also check it — but the Maker≠Checker constraint prevents this.
    # Still, dedupe by ID just in case.
    seen = set()
    unique = []
    for item in items:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        unique.append(item)

    unique.sort(key=lambda x: x["updated_at"], reverse=True)
    return unique
