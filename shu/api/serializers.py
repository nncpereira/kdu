from rest_framework import serializers
from shu.models import ShuCalculation, ShuMemberPayout


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
