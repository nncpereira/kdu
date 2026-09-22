from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMember
from loans.models import Loan
from members.api.serializers import MemberSerializer, UpdateMyMemberSerializer
from savings.models import MemberVoluntaryDeposit, Transaction as SavingsTxn
from savings.api.serializers import (
    TransactionSerializer,
    VoluntaryDepositSerializer,
)
from shu.models import ShuMemberPayout
from shu.api.serializers import MyShuPayoutSerializer


def _get_member(request):
    """Return the Member linked to the authenticated user, or None."""
    return getattr(request.user, "member_profile", None)


# ====================================================================
# Dashboard
# ====================================================================
class MyDashboardView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        member = _get_member(request)
        if not member:
            return Response(
                {"detail": "No member profile linked."},
                status=status.HTTP_404_NOT_FOUND,
            )

        vd = MemberVoluntaryDeposit.objects.filter(member=member).first()
        voluntary = vd.balance_available if vd else Decimal("0.00")
        held = vd.balance_held_pipeline if vd else Decimal("0.00")

        active_loans = Loan.objects.filter(member=member, status="DISBURSED")
        outstanding = active_loans.aggregate(t=Sum("principal_outstanding"))[
            "t"
        ] or Decimal("0.00")

        recent = list(
            SavingsTxn.objects.filter(member=member)
            .order_by("-created_at")
            .values(
                "id",
                "transaction_type",
                "requested_amount",
                "status",
                "created_at",
            )[:5]
        )

        return Response(
            {
                "member": {
                    "membership_number": member.membership_number,
                    "full_name": member.full_name,
                    "status": member.status,
                    "date_joined": member.date_joined,
                },
                "capital": str(member.kapital_sosial_balance),
                "voluntary": str(voluntary),
                "voluntary_held": str(held),
                "total_savings": str(member.kapital_sosial_balance + voluntary),
                "loans": {
                    "active_count": active_loans.count(),
                    "outstanding_total": str(outstanding),
                },
                "recent_activity": [
                    {
                        "id": str(r["id"]),
                        "type": r["transaction_type"],
                        "amount": str(r["requested_amount"]),
                        "status": r["status"],
                        "created_at": r["created_at"].isoformat(),
                    }
                    for r in recent
                ],
            }
        )


# ====================================================================
# Profile
# ====================================================================
class MyProfileView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        member = _get_member(request)
        if not member:
            return Response({"detail": "No member profile linked."}, status=404)
        return Response(MemberSerializer(member).data)

    @transaction.atomic
    def patch(self, request):
        member = _get_member(request)
        if not member:
            return Response({"detail": "No member profile linked."}, status=404)

        serializer = UpdateMyMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(member, field, value)
        member.save(
            update_fields=list(serializer.validated_data.keys()) + ["updated_at"]
        )

        return Response(MemberSerializer(member).data)


# ====================================================================
# Savings
# ====================================================================
class MySavingsView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        member = _get_member(request)
        if not member:
            return Response({"detail": "No member profile linked."}, status=404)

        vd = MemberVoluntaryDeposit.objects.filter(member=member).first()
        return Response(
            {
                "kapital_sosial_balance": str(member.kapital_sosial_balance),
                "voluntary": (
                    VoluntaryDepositSerializer(vd).data
                    if vd
                    else {
                        "member": str(member.id),
                        "balance_available": "0.00",
                        "balance_held_pipeline": "0.00",
                        "updated_at": None,
                    }
                ),
            }
        )


class MyTransactionsView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        member = _get_member(request)
        if not member:
            return Response({"detail": "No member profile linked."}, status=404)
        qs = SavingsTxn.objects.filter(member=member).order_by("-created_at")[:200]
        return Response(TransactionSerializer(qs, many=True).data)


# ====================================================================
# Loans
# ====================================================================
class MyLoansView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        member = _get_member(request)
        if not member:
            return Response({"detail": "No member profile linked."}, status=404)

        loans = Loan.objects.filter(member=member).order_by("-created_at")
        return Response(
            [
                {
                    "id": str(loan.id),
                    "principal_original": str(loan.principal_original),
                    "principal_outstanding": str(loan.principal_outstanding),
                    "monthly_rate": str(loan.monthly_rate),
                    "term_months": loan.term_months,
                    "purpose": loan.purpose,
                    "status": loan.status,
                    "disbursed_date": loan.disbursed_date,
                    "created_at": loan.created_at,
                }
                for loan in loans
            ]
        )


# ====================================================================
# SHU Statement
# ====================================================================
class MyShuStatementView(APIView):
    permission_classes = [IsMember]

    def get(self, request, year=None):
        member = _get_member(request)
        if not member:
            return Response({"detail": "No member profile linked."}, status=404)

        payouts = (
            ShuMemberPayout.objects.filter(member=member)
            .select_related("calc", "calc__fy")
            .order_by("-calc__fy__year_end")
        )
        return Response(MyShuPayoutSerializer(payouts, many=True).data)
