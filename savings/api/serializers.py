from decimal import Decimal

from rest_framework import serializers
from savings.models import Transaction, MemberVoluntaryDeposit


class TransactionSerializer(serializers.ModelSerializer):
    member_number = serializers.CharField(
        source="member.membership_number", read_only=True
    )

    class Meta:
        model = Transaction
        fields = [
            "id",
            "member",
            "member_number",
            "transaction_type",
            "requested_amount",
            "obligatory_portion",
            "voluntary_portion",
            "status",
            "pipeline_actor",
            "journal_entry",
            "created_at",
        ]
        read_only_fields = [
            "status",
            "pipeline_actor",
            "journal_entry",
            "obligatory_portion",
            "voluntary_portion",
        ]


class DepositRequestSerializer(serializers.Serializer):
    member = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )


class WithdrawRequestSerializer(serializers.Serializer):
    member = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )


class VoluntaryDepositSerializer(serializers.ModelSerializer):
    updated_at = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta:
        model = MemberVoluntaryDeposit
        fields = [
            "member",
            "balance_available",
            "balance_held_pipeline",
            "updated_at",
        ]
        read_only_fields = fields
