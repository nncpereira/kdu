from decimal import Decimal

from rest_framework import serializers

from loans.models import Loan, LoanRepayment


class LoanSerializer(serializers.ModelSerializer):
    member_number = serializers.CharField(
        source="member.membership_number", read_only=True
    )

    class Meta:
        model = Loan
        fields = [
            "id",
            "member",
            "member_number",
            "principal_original",
            "principal_outstanding",
            "monthly_rate",
            "term_months",
            "purpose",
            "disbursed_date",
            "status",
            "created_at",
        ]
        read_only_fields = ["principal_outstanding", "disbursed_date", "status"]


class LoanOriginateSerializer(serializers.Serializer):
    member = serializers.UUIDField()
    principal = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=Decimal("0.01")
    )
    term_months = serializers.IntegerField(min_value=1)
    monthly_rate = serializers.DecimalField(max_digits=6, decimal_places=4)
    purpose = serializers.CharField(required=False, allow_blank=True, default="")


class ManualRepaymentSerializer(serializers.Serializer):
    principal_paid = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=0
    )
    interest_paid = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=0
    )
    payment_date = serializers.DateField(required=False)


class ScheduledRepaymentSerializer(serializers.Serializer):
    cash_amount = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=Decimal("0.01")
    )
    scheduled_principal = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=0
    )
    payment_date = serializers.DateField(required=False)


class LoanRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanRepayment
        fields = [
            "id",
            "loan",
            "principal_paid",
            "interest_paid",
            "payment_date",
            "mode",
            "status",
            "journal_entry",
            "created_at",
        ]
