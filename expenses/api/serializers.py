from decimal import Decimal

from rest_framework import serializers

from expenses.models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    receipt_url = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = (
            "id",
            "description",
            "amount",
            "expense_account_code",
            "payment_date",
            "status",
            "journal_entry",
            "receipt",
            "receipt_url",
            "created_at",
        )
        read_only_fields = ("status", "journal_entry", "receipt_url")

    def get_receipt_url(self, obj):
        if not obj.receipt:
            return None
        request = self.context.get("request")
        url = obj.receipt.url
        return request.build_absolute_uri(url) if request else url


class ExpenseCreateSerializer(serializers.Serializer):
    description = serializers.CharField()
    amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    expense_account_code = serializers.CharField(max_length=20)
    payment_date = serializers.DateField(required=False)
    receipt = serializers.FileField(required=False, allow_null=True)
