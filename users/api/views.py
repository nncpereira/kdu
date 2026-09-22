from django.contrib.auth import update_session_auth_hash
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsSuperadmin
from users.api.serializers import (
    StaffUserSerializer,
    CreateStaffUserSerializer,
    UpdateStaffUserSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    UpdateMyProfileSerializer,
)
from users.models import UserProfile
from users.services import (
    create_staff_user,
    issue_temp_password,
    set_staff_active,
    update_staff_profile,
)

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user.profile).data)

    def patch(self, request):
        serializer = UpdateMyProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        update_fields = []
        for field in ("first_name", "last_name", "email"):
            if field in serializer.validated_data:
                setattr(user, field, serializer.validated_data[field])
                update_fields.append(field)

        if update_fields:
            user.save(update_fields=update_fields)

        return Response(UserProfileSerializer(user.profile).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        update_session_auth_hash(request, user)

        profile = user.profile
        profile.must_change_password = False
        profile.save(update_fields=["must_change_password"])

        return Response({"detail": "Password updated."}, status=status.HTTP_200_OK)


# ====================================================================
# Superadmin staff management
# ====================================================================
class StaffUserListCreateView(APIView):
    permission_classes = [IsSuperadmin]

    def get(self, request):
        qs = (
            UserProfile.objects.select_related("user")
            .exclude(role=UserProfile.Role.MEMBER)
            .order_by("role", "user__username")
        )
        return Response(StaffUserSerializer(qs, many=True).data)

    def post(self, request):
        serializer = CreateStaffUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile = create_staff_user(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
            role=serializer.validated_data["role"],
            email=serializer.validated_data.get("email", ""),
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
            actor=request.user.profile,
            request=request,
        )

        # Force password change on first login.
        profile.must_change_password = True
        profile.save(update_fields=["must_change_password"])

        return Response(
            StaffUserSerializer(profile).data,
            status=status.HTTP_201_CREATED,
        )


class StaffUserDetailView(APIView):
    permission_classes = [IsSuperadmin]

    def get(self, request, pk):
        profile = UserProfile.objects.select_related("user").get(pk=pk)
        return Response(StaffUserSerializer(profile).data)

    def patch(self, request, pk):
        profile = UserProfile.objects.select_related("user").get(pk=pk)
        serializer = UpdateStaffUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        update_staff_profile(profile, **serializer.validated_data)
        profile.refresh_from_db()
        return Response(StaffUserSerializer(profile).data)


class StaffUserDisableView(APIView):
    permission_classes = [IsSuperadmin]

    def post(self, request, pk):
        profile = UserProfile.objects.select_related("user").get(pk=pk)

        # Safety: cannot disable yourself.
        if profile.user_id == request.user.id:
            return Response(
                {"detail": "You cannot disable your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        set_staff_active(
            profile,
            False,
            actor=request.user.profile,
            request=request,
        )
        profile.refresh_from_db()
        return Response(StaffUserSerializer(profile).data)


class StaffUserEnableView(APIView):
    permission_classes = [IsSuperadmin]

    def post(self, request, pk):
        profile = UserProfile.objects.select_related("user").get(pk=pk)
        set_staff_active(
            profile,
            True,
            actor=request.user.profile,
            request=request,
        )
        profile.refresh_from_db()
        return Response(StaffUserSerializer(profile).data)


class StaffUserResetPasswordView(APIView):
    permission_classes = [IsSuperadmin]

    def post(self, request, pk):
        profile = UserProfile.objects.select_related("user").get(pk=pk)
        temp = issue_temp_password(
            profile.user,
            actor=request.user.profile,
            request=request,
        )
        return Response(
            {
                "detail": "Temporary password issued. Share it securely; the user must change it on next login.",
                "temporary_password": temp,
            }
        )
