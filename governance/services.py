from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction

from core.exceptions import LegalReserveViolationError
from governance.models import GlobalConfig, GlobalConfigChange
from ledger.services import account_net_balance

REQUIRED_KEYS = {
    "shu_split",
    "obligatory_savings_monthly_cap",
    "loan_interest_rate_range",
}


def get_active_config(parameter_key: str, as_of=None):
    """Return the active GlobalConfig row for a key."""
    qs = GlobalConfig.objects.filter(parameter_key=parameter_key, status="ACTIVE")
    if as_of:
        qs = qs.filter(effective_from__lte=as_of)
    return qs.order_by("-effective_from").first()


def get_active_value(parameter_key: str, as_of=None):
    row = get_active_config(parameter_key, as_of=as_of)
    return row.parameter_value if row else None


# --------------------------------------------------------------------
# Validation rules (DL 16/2004 Art. 69 as amended by DL 76/2022)
# --------------------------------------------------------------------
def validate_shu_split(proposed: dict):
    """
    Reserva Legal must be >= 25% until accumulated reserve reaches
    100% of Kapital Sosial (account 3101).
    """
    pct = Decimal(str(proposed.get("reserva_legal_pct", 0)))

    kapital = account_net_balance("3101")  # Kapital Sosial
    reserva = account_net_balance("3501")  # Reserva Legal

    if reserva < kapital and pct < Decimal("25"):
        raise LegalReserveViolationError(
            "Reserva Legal must be >= 25% until it reaches 100% "
            "of Social Capital (DL 76/2022 Art.69)."
        )

    total = (
        Decimal(str(proposed["reserva_legal_pct"]))
        + Decimal(str(proposed["admin_fund_pct"]))
        + Decimal(str(proposed["jasa_simpanan_pct"]))
        + Decimal(str(proposed["jasa_bunga_pct"]))
    )
    if total != Decimal("100"):
        raise ValidationError("SHU split percentages must sum to 100.")


_VALIDATORS = {
    "shu_split": validate_shu_split,
}


# --------------------------------------------------------------------
# Change workflow
# --------------------------------------------------------------------
@transaction.atomic
def propose_change(
    parameter_key: str, proposed_value: dict, effective_from, maker_user
):
    """Maker proposes a configuration change."""
    if parameter_key not in REQUIRED_KEYS:
        raise ValidationError(f"Unknown parameter: {parameter_key}")

    validator = _VALIDATORS.get(parameter_key)
    if validator:
        validator(proposed_value)

    change = GlobalConfigChange.objects.create(
        parameter_key=parameter_key,
        proposed_value=proposed_value,
        effective_from=effective_from,
        status=GlobalConfigChange.Status.PENDING_CHECK,
        created_by=maker_user,
    )
    return change


@transaction.atomic
def certify_change(change: GlobalConfigChange, certifier_user):
    """Certifier approves; write to append-only GlobalConfig."""
    if change.status != GlobalConfigChange.Status.PENDING_CERTIFY:
        raise ValidationError("Change must be in PENDING_CERTIFY state.")

    # Supersede previous active row for the same key
    GlobalConfig.objects.filter(
        parameter_key=change.parameter_key, status="ACTIVE"
    ).update(status="SUPERSEDED")

    GlobalConfig.objects.create(
        parameter_key=change.parameter_key,
        parameter_value=change.proposed_value,
        effective_from=change.effective_from,
        status="ACTIVE",
        created_by=certifier_user,
    )

    change.status = GlobalConfigChange.Status.CERTIFIED
    change.save()
    return change
