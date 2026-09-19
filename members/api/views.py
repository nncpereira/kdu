from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from core.pagination import StandardPagination

from core.permissions import IsMaker, IsStaffReadMembers
from members.api.serializers import (
    MemberSerializer,
    MemberCreateSerializer,
    InitialCapitalSerializer,
    MemberExitSerializer,
)
from members.models import Member, MemberOnboarding, MemberExitRequest
from members.services import onboard_member, pay_initial_capital, request_exit


class MemberListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsMaker()]
        return [IsStaffReadMembers()]

    def get(self, request):
        qs = Member.objects.all().order_by("membership_number")
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(MemberSerializer(page, many=True).data)

    def post(self, request):
        serializer = MemberCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = onboard_member(
            maker_user=request.user.profile,
            **serializer.validated_data,
        )
        return Response(MemberSerializer(member).data, status=status.HTTP_201_CREATED)


class MemberDetailView(APIView):
    permission_classes = [IsStaffReadMembers]

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        return Response(MemberSerializer(member).data)


class PayInitialCapitalView(APIView):
    permission_classes = [IsMaker]

    def post(self, request, pk):
        member = Member.objects.get(pk=pk)
        serializer = InitialCapitalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        onboarding = pay_initial_capital(
            member=member,
            amount=serializer.validated_data["amount"],
            maker_user=request.user.profile,
        )
        return Response(
            {
                "onboarding_id": str(onboarding.id),
                "pipeline_actor_id": str(onboarding.pipeline_actor_id),
            },
            status=status.HTTP_201_CREATED,
        )


class MemberExitView(APIView):
    permission_classes = [IsMaker]

    def post(self, request, pk):
        member = Member.objects.get(pk=pk)
        serializer = MemberExitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exit_req = request_exit(member=member, maker_user=request.user.profile)
        return Response(
            {
                "exit_request_id": str(exit_req.id),
                "pipeline_actor_id": str(exit_req.pipeline_actor_id),
            },
            status=status.HTTP_201_CREATED,
        )
