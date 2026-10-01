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


class JournalLineSerializer(serializers.Serializer):
    """
    A single debit/credit leg of a journal entry, with the account
    name resolved separately since account_code is a plain string,
    not a foreign key.
    """

    id = serializers.UUIDField()
    account_code = serializers.CharField()
    account_name = serializers.CharField()
    entry_type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    member_id = serializers.UUIDField(allow_null=True)
    member_number = serializers.CharField(allow_null=True)
    member_name = serializers.CharField(allow_null=True)


class JournalEntryDetailSerializer(serializers.Serializer):
    """
    Full detail of a single journal entry, including its debit/credit lines.
    """

    id = serializers.UUIDField()
    entry_date = serializers.DateField()
    description = serializers.CharField()
    status = serializers.CharField()
    maker_username = serializers.CharField(allow_null=True)
    certifier_username = serializers.CharField(allow_null=True)
    is_reversal = serializers.BooleanField()
    original_journal_entry = serializers.UUIDField(allow_null=True)
    created_at = serializers.DateTimeField()
    lines = JournalLineSerializer(many=True)
