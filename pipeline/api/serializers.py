from rest_framework import serializers

from pipeline.models import TransactionPipelineActor
from pipeline.summaries import get_summary


class PipelineActorSerializer(serializers.ModelSerializer):
    maker_username = serializers.CharField(source="maker.user.username", read_only=True)
    checker_username = serializers.CharField(
        source="checker.user.username", read_only=True, allow_null=True
    )
    certifier_username = serializers.CharField(
        source="certifier.user.username", read_only=True, allow_null=True
    )
    target_summary = serializers.SerializerMethodField()

    class Meta:
        model = TransactionPipelineActor
        fields = [
            "id",
            "transaction_type",
            "target_record_id",
            "maker",
            "maker_username",
            "checker",
            "checker_username",
            "certifier",
            "certifier_username",
            "status",
            "updated_at",
            "target_summary",
        ]

    def get_target_summary(self, obj):
        return get_summary(obj.transaction_type, obj.target_record_id)
