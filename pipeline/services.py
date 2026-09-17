from django.core.exceptions import ValidationError
from django.db import transaction

from pipeline.models import TransactionPipelineActor
from pipeline.registry import get_handlers


# ====================================================================
# Creation
# ====================================================================
@transaction.atomic
def create_pipeline(*, transaction_type, target_record_id, maker_user):
    """
    Create a pipeline actor in PENDING_CHECK status.
    """

    actor = TransactionPipelineActor.objects.create(
        transaction_type=transaction_type,
        target_record_id=target_record_id,
        maker=maker_user,
        status=TransactionPipelineActor.Status.PENDING_CHECK,
    )
    return actor


# ====================================================================
# Checker step
# ====================================================================
@transaction.atomic
def check(actor: TransactionPipelineActor, checker_user):
    if actor.status != TransactionPipelineActor.Status.PENDING_CHECK:
        raise ValidationError(
            f"Actor is not awaiting check (current status: {actor.status})."
        )
    if actor.maker == checker_user:
        raise ValidationError("Maker cannot be the Checker on the same transaction.")

    actor.checker = checker_user
    actor.status = TransactionPipelineActor.Status.PENDING_CERTIFY
    actor.save(update_fields=["checker", "status", "updated_at"])

    for handler in get_handlers(actor.transaction_type, "on_check"):
        handler(actor, checker_user)

    return actor


# ====================================================================
# Certifier step
# ====================================================================
@transaction.atomic
def certify(actor: TransactionPipelineActor, certifier_user):
    if actor.status != TransactionPipelineActor.Status.PENDING_CERTIFY:
        raise ValidationError(
            f"Actor is not awaiting certification (current status: {actor.status})."
        )
    if actor.maker == certifier_user or actor.checker == certifier_user:
        raise ValidationError(
            "Certifier must be a distinct user from Maker and Checker."
        )

    actor.certifier = certifier_user
    actor.status = TransactionPipelineActor.Status.COMPLETED
    actor.save(update_fields=["certifier", "status", "updated_at"])

    # Fire domain-specific completion handlers
    for handler in get_handlers(actor.transaction_type, "on_certify"):
        handler(actor, certifier_user)
    return actor


# ====================================================================
# Reject
# ====================================================================
@transaction.atomic
def reject(actor: TransactionPipelineActor, rejector_user, reason: str=""):
    if actor.status not in (
        TransactionPipelineActor.Status.PENDING_CHECK,
        TransactionPipelineActor.Status.PENDING_CERTIFY,
    ):
        raise ValidationError("Only pending actors can be rejected.")

    actor.status = TransactionPipelineActor.Status.REJECTED
    actor.rejection_reason = reason or ""
    actor.save(update_fields=["status", "rejection_reason", "updated_at"])

    for handler in get_handlers(actor.transaction_type, "on_reject"):
        handler(actor, rejector_user, reason)
    return actor
