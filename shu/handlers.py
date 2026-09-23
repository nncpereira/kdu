from django.db import transaction

from pipeline.registry import register
from shu.models import ShuCalculation
from shu.services.calculation import compute_member_payouts
from shu.services.payout import finalise_payout


@register("SHU_CALCULATE", "on_check")
@transaction.atomic
def on_shu_checked(actor, checker_user):
    calc = ShuCalculation.objects.select_for_update().get(pk=actor.target_record_id)
    compute_member_payouts(calc)
    calc.status = ShuCalculation.Status.PENDING_CERTIFY
    calc.save(update_fields=["status", "updated_at"])


@register("SHU_CALCULATE", "on_certify")
@transaction.atomic
def on_shu_certified(actor, certifier_user):
    calc = ShuCalculation.objects.select_for_update().get(pk=actor.target_record_id)
    calc.status = ShuCalculation.Status.CERTIFIED
    calc.save(update_fields=["status", "updated_at"])
    finalise_payout(calc, certifier_user)


@register("SHU_CALCULATE", "on_reject")
@transaction.atomic
def on_shu_rejected(actor, rejector_user, reason):
    calc = ShuCalculation.objects.select_for_update().get(pk=actor.target_record_id)
    calc.status = ShuCalculation.Status.REJECTED
    calc.save(update_fields=["status", "updated_at"])
