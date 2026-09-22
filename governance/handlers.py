from pipeline.registry import register
from governance.models import GlobalConfigChange


def _change(actor):
    return GlobalConfigChange.objects.filter(pipeline_actor=actor).first()


@register("CONFIG_CHANGE", "on_check")
def on_config_checked(actor, checker_user):
    change = _change(actor)
    if change:
        change.status = GlobalConfigChange.Status.PENDING_CERTIFY
        change.save(update_fields=["status", "updated_at"])


@register("CONFIG_CHANGE", "on_reject")
def on_config_rejected(actor, rejector_user, reason=""):
    change = _change(actor)
    if change:
        change.status = GlobalConfigChange.Status.REJECTED
        change.save(update_fields=["status", "updated_at"])
