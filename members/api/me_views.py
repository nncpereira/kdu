from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMember
from loans.api.serializers import LoanRepaymentSerializer
from loans.models import Loan, LoanRepayment
from members.api.serializers import MemberSerializer, UpdateMyMemberSerializer
from savings.api.serializers import VoluntaryDepositSerializer
from savings.models import MemberVoluntaryDeposit
from savings.models import Transaction as SavingsTxn
from shu.api.serializers import MyShuPayoutSerializer
from shu.models import ShuMemberPayout


def _get_member(request):
    """Return the Member linked to the authenticated user, or None."""
    return getattr(request.user, "member_profile", None)


# ====================================================================
# Dashboard
# ====================================================================
class MyDashboardView(APIView):
    permission_classes = [IsMember]

    @extend_schema(
        responses={200: OpenApiResponse(description="Member dashboard summary.")},
        tags=["member-portal"],
        summary="Member's own dashboard",
    )
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

    @extend_schema(
        responses={200: MemberSerializer},
        tags=["member-portal"],
        summary="Member's own profile",
    )
    def get(self, request):
        member = _get_member(request)
        if not member:
            return Response({"detail": "No member profile linked."}, status=404)
        return Response(MemberSerializer(member).data)

    @transaction.atomic
    @extend_schema(
        request=UpdateMyMemberSerializer,
        responses={200: MemberSerializer},
        tags=["member-portal"],
        summary="Update member's own contact details",
    )
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

    @extend_schema(
        responses={200: OpenApiResponse(description="Member Savings summary.")},
        tags=["member-portal"],
        summary="Member's own savings",
    )
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
    """
    Unified history mirroring the admin member-detail "Transaction History"
    table: savings deposits/withdrawals plus initial capital, exit refunds,
    and loan-repayment cash swept into the member's own savings -- not just
    the raw savings ledger, which was missing those event types.
    """

    permission_classes = [IsMember]

    @extend_schema(
        responses={200: OpenApiResponse(description="Member Transaction summary.")},
        tags=["member-portal"],
        summary="Member's own transactions",
    )
    def get(self, request):
        member = _get_member(request)
        if not member:
            return Response({"detail": "No member profile linked."}, status=404)

        rows = [
            {
                "id": str(o.id),
                "date": o.created_at,
                "event": "Initial Capital",
                "amount": str(o.initial_capital_amount),
                "status": o.status,
            }
            for o in member.onboardings.all()
        ]
        rows += [
            {
                "id": str(e.id),
                "date": e.created_at,
                "event": "Capital Refund (Exit)",
                "amount": str(e.refund_amount),
                "status": e.status,
            }
            for e in member.exit_requests.all()
        ]
        rows += [
            {
                "id": str(t.id),
                "date": t.created_at,
                "event": "Deposit" if t.transaction_type == "DEPOSIT" else "Withdrawal",
                "amount": str(t.requested_amount),
                "status": t.status,
            }
            for t in SavingsTxn.objects.filter(member=member)
        ]
        sweeps = LoanRepayment.objects.filter(loan__member=member).filter(
            Q(obligatory_portion__gt=0) | Q(voluntary_portion__gt=0)
        )
        rows += [
            {
                "id": str(s.id),
                "date": s.created_at,
                "event": "Loan Repayment → Savings",
                "amount": str(s.obligatory_portion + s.voluntary_portion),
                "status": s.status,
            }
            for s in sweeps
        ]

        rows.sort(key=lambda r: r["date"], reverse=True)
        return Response(rows[:200])


# ====================================================================
# Loans
# ====================================================================
class MyLoansView(APIView):
    permission_classes = [IsMember]

    @extend_schema(
        responses={200: OpenApiResponse(description="Member Loans summary.")},
        tags=["member-portal"],
        summary="Member's own loans",
    )
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


class MyLoanRepaymentsView(APIView):
    permission_classes = [IsMember]

    @extend_schema(
        responses={200: LoanRepaymentSerializer(many=True)},
        tags=["member-portal"],
        summary="Repayment history for one of the member's own loans",
    )
    def get(self, request, loan_id):
        member = _get_member(request)
        if not member:
            return Response({"detail": "No member profile linked."}, status=404)

        loan = get_object_or_404(Loan, pk=loan_id, member=member)
        qs = LoanRepayment.objects.filter(
            loan=loan, status=LoanRepayment.Status.COMPLETED
        ).order_by("-payment_date")
        return Response(LoanRepaymentSerializer(qs, many=True).data)


# ====================================================================
# SHU Statement
# ====================================================================
class MyShuStatementView(APIView):
    permission_classes = [IsMember]

    @extend_schema(
        responses={200: OpenApiResponse(description="Member SHU Statement summary.")},
        tags=["member-portal"],
        summary="Member's own SHU statement",
    )
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
