from rest_framework import serializers


class TrialBalanceRowSerializer(serializers.Serializer):
    account_code = serializers.CharField()
    account_name = serializers.CharField()
    account_type = serializers.CharField()
    debit = serializers.DecimalField(max_digits=18, decimal_places=2)
    credit = serializers.DecimalField(max_digits=18, decimal_places=2)
    net = serializers.DecimalField(max_digits=18, decimal_places=2)
