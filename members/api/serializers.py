from rest_framework import serializers
from members.models import Member, MemberOnboarding, MemberExitRequest


class MemberSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Member
        fields = [
            "id",
            "membership_number",
            "salutation",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "national_id",
            "phone_number",
            "email",
            "date_of_birth",
            "aldeia",
            "suco",
            "posto",
            "municipio",
            "profession",
            "status",
            "kapital_sosial_balance",
            "date_joined",
            "last_transaction_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "membership_number",
            "kapital_sosial_balance",
            "status",
        ]


class MemberCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    middle_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField()
    salutation = serializers.CharField(required=False, default="Mr")
    national_id = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    phone_number = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    date_of_birth = serializers.DateField()
    aldeia = serializers.CharField(required=False, allow_blank=True, default="")
    suco = serializers.CharField(required=False, allow_blank=True, default="")
    posto = serializers.CharField(required=False, allow_blank=True, default="")
    municipio = serializers.CharField(required=False, allow_blank=True, default="")
    profession = serializers.CharField(required=False, allow_blank=True, default="")


class InitialCapitalSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)


class MemberExitSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")
