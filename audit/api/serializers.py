from rest_framework import serializers

from audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(
        source="actor.user.username", read_only=True, allow_null=True
    )
    actor_role = serializers.CharField(
        source="actor.role", read_only=True, allow_null=True
    )

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor",
            "actor_username",
            "actor_role",
            "action",
            "target_type",
            "target_id",
            "target_repr",
            "description",
            "metadata",
            "ip_address",
            "user_agent",
            "created_at",
        ]
        read_only_fields = fields


class LedgerActivitySerializer(serializers.Serializer):
    """
    Read-only view of a certified JournalEntry, aggregating the
    entry itself with its maker and certifier.
    """

    id = serializers.UUIDField()
    entry_date = serializers.DateField()
    description = serializers.CharField()
    maker_username = serializers.CharField(allow_null=True)
    certifier_username = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    line_count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    is_reversal = serializers.BooleanField()
    created_at = serializers.DateTimeField()
