from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from core.exceptions import LegalReserveViolationError
from governance.models import GlobalConfig, GlobalConfigChange
from ledger.services import account_net_balance

from audit.services import record_audit
from pipeline.services import create_pipeline

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
SHU_SPLIT_KEYS = (
    "reserva_legal_pct",
    "admin_fund_pct",
    "jasa_simpanan_pct",
    "jasa_bunga_pct",
)


# def _json_safe(value):
#     """Convert DRF Decimal values to JSON-compatible strings."""
#     if isinstance(value, Decimal):
#         return int(value) if value == value.to_integral_value() else float(value)
#     if isinstance(value, dict):
#         return {key: _json_safe(item) for key, item in value.items()}
#     if isinstance(value, list):
#         return [_json_safe(item) for item in value]
#     return value


def _require_number(mapping: dict, key: str) -> Decimal:
    """
    Extract a numeric field from `mapping`, raising a clean
    ValidationError (not a KeyError / ValueError) if it's missing
    or not a valid number.
    """
    if key not in mapping:
        raise ValidationError({key: "This field is required."})

    raw = mapping[key]
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError({key: "Must be a number."})

    return value


def validate_shu_split(proposed: dict) -> None:
    """
    Validate the SHU split shape and the DL 76/2022 Art. 69 constraint.

    Raises ValidationError (400-friendly) for any problem, never a
    KeyError or a bare arithmetic error.
    """
    if not isinstance(proposed, dict):
        raise ValidationError({"proposed_value": "Must be a JSON object."})

    # ---- Shape ----------------------------------------------------
    values = {key: _require_number(proposed, key) for key in SHU_SPLIT_KEYS}

    # ---- Range ----------------------------------------------------
    for key, value in values.items():
        if value < 0 or value > 100:
            raise ValidationError({key: "Percentage must be between 0 and 100."})

    # ---- Sum ------------------------------------------------------
    total = sum(values.values())
    if total != Decimal("100"):
        raise ValidationError(
            {
                "proposed_value": (
                    f"Percentages must sum to 100. Current total: {total}."
                )
            }
        )

    # ---- Art. 69 (DL 76/2022) ------------------------------------
    kapital = account_net_balance("3101")  # Kapital Sosial
    reserva = account_net_balance("3501")  # Reserva Legal

    if reserva < kapital and values["reserva_legal_pct"] < Decimal("25"):
        raise LegalReserveViolationError(
            "Reserva Legal must be >= 25% until it reaches 100% "
            "of Social Capital (DL 76/2022 Art.69)."
        )

def validate_obligatory_savings_cap(proposed: dict) -> None:
    """Validates the {value: N} shape for obligatory_savings_monthly_cap."""
    if not isinstance(proposed, dict):
        raise ValidationError({"proposed_value": "Must be a JSON object."})
    value = _require_number(proposed, "value")
    if value < 0:
        raise ValidationError({"value": "Must be a non-negative number."})
    if value > Decimal("10000"):
        raise ValidationError({"value": "Cap seems unreasonably high."})


def validate_loan_interest_range(proposed: dict) -> None:
    """Validates the {min: X, max: Y} shape for loan_interest_rate_range."""
    if not isinstance(proposed, dict):
        raise ValidationError({"proposed_value": "Must be a JSON object."})
    lo = _require_number(proposed, "min")
    hi = _require_number(proposed, "max")
    if lo < 0 or hi < 0:
        raise ValidationError("Rates must be non-negative.")
    if lo > hi:
        raise ValidationError(
            {"proposed_value": "min must be less than or equal to max."}
        )
    if hi > Decimal("1"):
        raise ValidationError({"max": "Monthly rate above 100% is not permitted."})


# Keep this registry after every validator definition so module import
# resolves each function before constructing the mapping.
_VALIDATORS = {
    "shu_split": validate_shu_split,
    "obligatory_savings_monthly_cap": validate_obligatory_savings_cap,
    "loan_interest_rate_range": validate_loan_interest_range,
}


# --------------------------------------------------------------------
# Change workflow
# --------------------------------------------------------------------
@transaction.atomic
def propose_change(
    parameter_key: str, proposed_value: dict, effective_from, maker_user, request=None
):
    """Maker proposes a configuration change."""
    if parameter_key not in REQUIRED_KEYS:
        raise ValidationError(f"Unknown parameter: {parameter_key}")

    validator = _VALIDATORS.get(parameter_key)
    if validator:
        validator(proposed_value)

    # proposed_value = _json_safe(proposed_value)
    change = GlobalConfigChange.objects.create(
        parameter_key=parameter_key,
        proposed_value=proposed_value,
        effective_from=effective_from,
        status=GlobalConfigChange.Status.PENDING_CHECK,
        created_by=maker_user,
    )
    actor = create_pipeline(
        transaction_type="CONFIG_CHANGE",
        target_record_id=change.id,
        maker_user=maker_user,
    )
    change.pipeline_actor = actor
    change.save(update_fields=["pipeline_actor", "updated_at"])

    if maker_user is not None:
        record_audit(
            actor=maker_user,
            action="CONFIG_PROPOSED",
            target_type="CONFIG_CHANGE",
            target_id=change.id,
            target_repr=parameter_key,
            description=f"Proposed change to {parameter_key}",
            metadata={
                "proposed_value": proposed_value,
                "effective_from": str(effective_from),
            },
            request=request,
        )
    return change


@transaction.atomic
def certify_change(change: GlobalConfigChange, certifier_user, request=None):
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

    if certifier_user is not None:
        record_audit(
            actor=certifier_user,
            action="CONFIG_CERTIFIED",
            target_type="CONFIG_CHANGE",
            target_id=change.id,
            target_repr=change.parameter_key,
            description=f"Certified change to {change.parameter_key}",
            metadata={"proposed_value": change.proposed_value},
            request=request,
        )
    return change
