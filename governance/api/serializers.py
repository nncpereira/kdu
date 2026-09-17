from rest_framework import serializers
from governance.models import GlobalConfig, GlobalConfigChange


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
