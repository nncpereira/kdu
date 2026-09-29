from rest_framework import serializers

from shu.models import ShuCalculation, ShuFiscalYear, ShuMemberPayout


class ShuMonthlyBalanceSerializer(serializers.Serializer):
    month_date = serializers.DateField()
    total_balance = serializers.DecimalField(max_digits=18, decimal_places=2)
    weight = serializers.IntegerField()
    weighted_balance = serializers.DecimalField(max_digits=18, decimal_places=2)
    eligible = serializers.BooleanField()


class ShuMemberPayoutDetailSerializer(serializers.Serializer):
    """
    Everything behind one member's payout: their weighting inputs, the
    monthly balances that produced them, and the pool totals needed to
    reproduce the proportional-split math by hand.
    """

    member_number = serializers.CharField()
    full_name = serializers.CharField()
    months_active = serializers.IntegerField()
    sum_weighted_balance = serializers.DecimalField(max_digits=18, decimal_places=2)
    weighted_savings_units = serializers.DecimalField(max_digits=18, decimal_places=2)
    loan_interest_paid = serializers.DecimalField(max_digits=18, decimal_places=2)
    monthly_balances = ShuMonthlyBalanceSerializer(many=True)

    total_weighted_savings_units = serializers.DecimalField(
        max_digits=18, decimal_places=2
    )
    total_loan_interest_paid = serializers.DecimalField(
        max_digits=18, decimal_places=2
    )
    jasa_simpanan_pool = serializers.DecimalField(max_digits=18, decimal_places=2)
    jasa_bunga_pool = serializers.DecimalField(max_digits=18, decimal_places=2)

    jasa_simpanan_gross = serializers.DecimalField(max_digits=18, decimal_places=2)
    jasa_bunga_gross = serializers.DecimalField(max_digits=18, decimal_places=2)
    net_payout = serializers.DecimalField(max_digits=18, decimal_places=2)


class ShuCalculationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShuCalculation
        fields = [
            "id",
            "fy",
            "net_surplus",
            "reserva_legal_pct",
            "admin_fund_pct",
            "jasa_simpanan_pct",
            "jasa_bunga_pct",
            "reserva_legal_amt",
            "admin_fund_amt",
            "jasa_simpanan_amt",
            "jasa_bunga_amt",
            "status",
            "created_at",
        ]


class ShuMemberPayoutSerializer(serializers.ModelSerializer):
    member_number = serializers.CharField(
        source="member.membership_number", read_only=True
    )
    full_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = ShuMemberPayout
        fields = [
            "id",
            "member",
            "member_number",
            "full_name",
            "jasa_simpanan_gross",
            "jasa_bunga_gross",
            "net_payout",
            "status",
        ]


class ShuFiscalYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShuFiscalYear
        fields = [
            "id",
            "year_start",
            "year_end",
            "status",
            "net_surplus",
            "kapital_sosial",
            "accumulated_reserva_legal",
            "created_at",
        ]
        read_only_fields = fields


class CreateFiscalYearSerializer(serializers.Serializer):
    year_start = serializers.DateField()
    year_end = serializers.DateField()


class MyShuPayoutSerializer(serializers.ModelSerializer):
    fiscal_year_start = serializers.DateField(
        source="calc.fy.year_start", read_only=True
    )
    fiscal_year_end = serializers.DateField(source="calc.fy.year_end", read_only=True)

    class Meta:
        model = ShuMemberPayout
        fields = [
            "id",
            "fiscal_year_start",
            "fiscal_year_end",
            "jasa_simpanan_gross",
            "jasa_bunga_gross",
            "net_payout",
            "status",
        ]
