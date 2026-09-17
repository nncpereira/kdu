from decimal import Decimal

from rest_framework import serializers
from expenses.models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = [
            "id",
            "description",
            "amount",
            "expense_account_code",
            "payment_date",
            "status",
            "created_at",
        ]
        read_only_fields = ["status"]


class ExpenseCreateSerializer(serializers.Serializer):
    description = serializers.CharField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))
    expense_account_code = serializers.CharField(max_length=20)
    payment_date = serializers.DateField(required=False)
