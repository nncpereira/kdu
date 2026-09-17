from rest_framework import serializers
from pipeline.models import TransactionPipelineActor


class PipelineActorSerializer(serializers.ModelSerializer):
    maker_username = serializers.CharField(source="maker.user.username", read_only=True)
    checker_username = serializers.CharField(
        source="checker.user.username", read_only=True, allow_null=True
    )
    certifier_username = serializers.CharField(
        source="certifier.user.username", read_only=True, allow_null=True
    )

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
        ]
