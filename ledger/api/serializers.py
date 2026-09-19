from rest_framework import serializers

from ledger.models import JournalEntry, ReversalRequest


class ReversalRequestSerializer(serializers.ModelSerializer):
    original_description = serializers.CharField(
        source="original_journal_entry.description", read_only=True
    )
    original_entry_date = serializers.DateField(
        source="original_journal_entry.entry_date", read_only=True
    )
    maker_username = serializers.CharField(
        source="pipeline_actor.maker.user.username", read_only=True, allow_null=True
    )

    class Meta:
        model = ReversalRequest
        fields = [
            "id",
            "pipeline_actor",
            "original_journal_entry",
            "original_description",
            "original_entry_date",
            "reversal_journal_entry",
            "source_type",
            "source_id",
            "reason",
            "status",
            "maker_username",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "reversal_journal_entry",
            "status",
            "maker_username",
            "created_at",
        ]


class CreateReversalSerializer(serializers.Serializer):
    original_journal_entry = serializers.UUIDField()
    source_type = serializers.ChoiceField(choices=ReversalRequest.SourceType.choices)
    source_id = serializers.UUIDField(required=False, allow_null=True)
    reason = serializers.CharField(min_length=5, max_length=500)
