from rest_framework import serializers

from loans.models import LoanRepayment
from members.models import Member, MemberExitRequest, MemberOnboarding


class MemberSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    has_login = serializers.SerializerMethodField()
    login_username = serializers.SerializerMethodField()

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
            "has_login",
            "login_username",
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
            "has_login",
            "login_username",
        ]

    def get_has_login(self, obj) -> bool:
        return bool(obj.user_id)

    def get_login_username(self, obj) -> str | None:
        return obj.user.username if obj.user_id else None


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


class UpdateMyMemberSerializer(serializers.Serializer):
    """
    Fields a member can edit about themselves.
    Excludes name, DOB, national_id, membership_number, status, capital
    — those are staff-managed or ledger-derived.
    """

    phone_number = serializers.CharField(max_length=20, required=False)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    aldeia = serializers.CharField(max_length=100, required=False, allow_blank=True)
    suco = serializers.CharField(max_length=100, required=False, allow_blank=True)
    posto = serializers.CharField(max_length=100, required=False, allow_blank=True)
    municipio = serializers.CharField(max_length=100, required=False, allow_blank=True)
    profession = serializers.CharField(max_length=100, required=False, allow_blank=True)


class InitialCapitalSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)


class MemberExitSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class MemberOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberOnboarding
        fields = [
            "id",
            "initial_capital_amount",
            "status",
            "created_at",
        ]


class MemberExitRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberExitRequest
        fields = [
            "id",
            "refund_amount",
            "status",
            "created_at",
        ]


class LoanRepaymentSweepSerializer(serializers.ModelSerializer):
    loan_id = serializers.UUIDField(source="loan.id", read_only=True)

    class Meta:
        model = LoanRepayment
        fields = [
            "id",
            "loan_id",
            "obligatory_portion",
            "voluntary_portion",
            "status",
            "created_at",
        ]


class MemberCapitalHistorySerializer(serializers.Serializer):
    onboardings = MemberOnboardingSerializer(many=True)
    exit_requests = MemberExitRequestSerializer(many=True)
    loan_repayment_sweeps = LoanRepaymentSweepSerializer(many=True)
