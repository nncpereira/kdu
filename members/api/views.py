from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from core.pagination import StandardPagination

from core.permissions import IsMaker, IsStaffReadMembers, IsSuperadmin
from members.api.serializers import (
    MemberSerializer,
    MemberCreateSerializer,
    InitialCapitalSerializer,
    MemberExitSerializer,
)
from members.models import Member, MemberOnboarding, MemberExitRequest
from members.services import onboard_member, pay_initial_capital, request_exit

from users.models import UserProfile
from users.services import create_member_user, issue_temp_password

from audit.services import record_audit


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


class CreateMemberLoginView(APIView):
    """
    Superadmin-only. Creates an auth user for a member and returns
    the temporary password ONCE. Idempotent for the user check.
    """
    permission_classes = [IsSuperadmin]

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk)

        if member.user_id:
            return Response(
                {
                    "detail": (
                        f"Member already has a login: "
                        f"{member.user.username}. "
                        f"Use Reset Password if needed."
                    ),
                    "login_username": member.user.username,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = create_member_user(member=member)

        record_audit(
            actor=request.user.profile,
            action="MEMBER_LOGIN_CREATED",
            target_type="MEMBER",
            target_id=member.id,
            target_repr=member.membership_number,
            description=f"Created portal login for member {member.membership_number}",
            metadata={"login_username": user.username},
            request=request,
        )

        return Response({
            "login_username": user.username,
            "temporary_password": user._temp_password,
            "detail": (
                "Login created. Share the temporary password securely. "
                "The member must change it on first login."
            ),
        }, status=status.HTTP_201_CREATED)


class ResetMemberLoginPasswordView(APIView):
    """
    Superadmin-only. Issues a new temporary password for a member's login.
    """
    permission_classes = [IsSuperadmin]

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk)

        if not member.user_id:
            return Response(
                {"detail": "Member has no login to reset."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        temp = issue_temp_password(member.user)

        record_audit(
            actor=request.user.profile,
            action="MEMBER_LOGIN_RESET",
            target_type="MEMBER",
            target_id=member.id,
            target_repr=member.membership_number,
            description=f"Reset portal password for member {member.membership_number}",
            request=request,
        )
        
        return Response({
            "login_username": member.user.username,
            "temporary_password": temp,
            "detail": (
                "Password reset. Share the temporary password securely."
            ),
        })
