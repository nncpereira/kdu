from django.contrib.auth import update_session_auth_hash
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.api.serializers import UserProfileSerializer, ChangePasswordSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user.profile).data)


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
