from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMember
from loans.models import Loan, LoanRepayment
from members.api.serializers import MemberSerializer
from savings.models import MemberVoluntaryDeposit, Transaction as SavingsTxn
from savings.api.serializers import (
    TransactionSerializer,
    VoluntaryDepositSerializer,
)
from shu.models import ShuMemberPayout
from shu.api.serializers import ShuMemberPayoutSerializer


def _get_member(request):
    return getattr(request.user, "member_profile", None)


class MyProfileView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        member = _get_member(request)
        if not member:
            return Response({"detail": "No member profile linked."}, status=404)
        return Response(MemberSerializer(member).data)


class MySavingsView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        member = _get_member(request)
        vd = MemberVoluntaryDeposit.objects.filter(member=member).first()
        payload = {
            "kapital_sosial_balance": str(member.kapital_sosial_balance),
            "voluntary": (
                VoluntaryDepositSerializer(vd).data
                if vd
                else {"balance_available": "0.00", "balance_held_pipeline": "0.00"}
            ),
        }
        return Response(payload)


class MyTransactionsView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        member = _get_member(request)
        qs = SavingsTxn.objects.filter(member=member).order_by("-created_at")[:200]
        return Response(TransactionSerializer(qs, many=True).data)


class MyLoansView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        member = _get_member(request)
        loans = Loan.objects.filter(member=member).order_by("-created_at")
        data = [
            {
                "id": str(l.id),
                "principal_original": str(l.principal_original),
                "principal_outstanding": str(l.principal_outstanding),
                "monthly_rate": str(l.monthly_rate),
                "term_months": l.term_months,
                "status": l.status,
                "disbursed_date": l.disbursed_date,
            }
            for l in loans
        ]
        return Response(data)


class MyShuStatementView(APIView):
    permission_classes = [IsMember]

    def get(self, request, year):
        member = _get_member(request)
        payouts = (
            ShuMemberPayout.objects.filter(member=member)
            .select_related("calc", "calc__fy")
            .order_by("-calc__fy__year_end")
        )
        return Response(ShuMemberPayoutSerializer(payouts, many=True).data)
