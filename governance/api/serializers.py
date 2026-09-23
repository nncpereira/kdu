from decimal import Decimal

from rest_framework import serializers

from governance.models import GlobalConfig, GlobalConfigChange


def _normalize_json(value):
    """
    Recursively convert Decimal to float so the value can be stored
    in a JSONField. Other types pass through unchanged.
    """
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: _normalize_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_json(v) for v in value]
    return value


class GlobalConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalConfig
        fields = ["id", "parameter_key", "parameter_value", "effective_from", "status"]


class GlobalConfigChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalConfigChange
        fields = [
            "id",
            "parameter_key",
            "proposed_value",
            "effective_from",
            "status",
            "created_at",
        ]
        read_only_fields = ["status", "created_at"]


SHU_SPLIT_KEYS = (
    "reserva_legal_pct",
    "admin_fund_pct",
    "jasa_simpanan_pct",
    "jasa_bunga_pct",
)


# ====================================================================
# Per-parameter shape validators
# ====================================================================
class ShuSplitValueSerializer(serializers.Serializer):
    """
    Validates the {reserva_legal_pct, admin_fund_pct, jasa_simpanan_pct,
    jasa_bunga_pct} object.
    """

    reserva_legal_pct = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, max_value=100
    )
    admin_fund_pct = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, max_value=100
    )
    jasa_simpanan_pct = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, max_value=100
    )
    jasa_bunga_pct = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, max_value=100
    )

    def validate(self, attrs):
        total = sum(attrs.values(), Decimal("0"))
        if total != Decimal("100"):
            raise serializers.ValidationError(
                f"Percentages must sum to 100. Current total: {total}."
            )
        return attrs


class LoanInterestRangeSerializer(serializers.Serializer):
    """Validates {min: X, max: Y}."""

    min = serializers.DecimalField(
        max_digits=6, decimal_places=4, min_value=0, max_value=1
    )
    max = serializers.DecimalField(
        max_digits=6, decimal_places=4, min_value=0, max_value=1
    )

    def validate(self, attrs):
        if attrs["min"] > attrs["max"]:
            raise serializers.ValidationError("min must be less than or equal to max.")
        return attrs


# ====================================================================
# Maps parameter_key -> shape serializer, for object-shaped values.
# obligatory_savings_monthly_cap is a bare number, so it's validated
# separately in ProposeChangeSerializer.validate() below.
# ====================================================================
SHAPE_VALIDATORS = {
    "shu_split": ShuSplitValueSerializer,
    "loan_interest_rate_range": LoanInterestRangeSerializer,
}


# ====================================================================
# The proposal serializer
# ====================================================================
class ProposeChangeSerializer(serializers.Serializer):
    parameter_key = serializers.ChoiceField(
        choices=[
            "shu_split",
            "obligatory_savings_monthly_cap",
            "loan_interest_rate_range",
        ]
    )
    proposed_value = serializers.JSONField()
    effective_from = serializers.DateField()

    def validate(self, attrs):
        """
        Validate proposed_value's shape against the parameter_key.
        A missing or wrong-shaped value fails here, cleanly, as a 400.
        """
        key = attrs.get("parameter_key")
        value = attrs.get("proposed_value")

        if key == "obligatory_savings_monthly_cap":
            field = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0)
            try:
                validated = field.run_validation(value)
            except serializers.ValidationError as exc:
                raise serializers.ValidationError({"proposed_value": exc.detail}) from None
            attrs["proposed_value"] = _normalize_json(validated)
            return attrs

        validator_cls = SHAPE_VALIDATORS.get(key)
        if validator_cls is None:
            # Unknown key — the ChoiceField above already blocks this,
            # but keep the guard for safety.
            raise serializers.ValidationError(
                {"parameter_key": f"Unsupported parameter: {key}"}
            )

        if not isinstance(value, dict):
            raise serializers.ValidationError(
                {"proposed_value": "Must be a JSON object."}
            )

        nested = validator_cls(data=value)
        if not nested.is_valid():
            # Attach the nested errors under proposed_value.
            raise serializers.ValidationError({"proposed_value": nested.errors})

        # Store the validated, normalised version so the service layer
        # receives a consistent shape.
        attrs["proposed_value"] = _normalize_json(nested.validated_data)

        return attrs
