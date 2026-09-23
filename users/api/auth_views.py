from django.conf import settings
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from audit.services import record_audit


class AccessTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()


class LogoutResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()

REFRESH_COOKIE_NAME = "kdu_refresh"
REFRESH_COOKIE_PATH = "/api/v1/auth/"


# ====================================================================
# Cookie helpers
# ====================================================================
def _cookie_max_age() -> int:
    return int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())


def _set_refresh_cookie(response, refresh_token: str):
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=_cookie_max_age(),
        httponly=True,
        secure=not settings.DEBUG,  # HTTPS-only in production
        samesite="Strict",
        path=REFRESH_COOKIE_PATH,  # only sent to the auth endpoints
    )


def _clear_refresh_cookie(response):
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        samesite="Strict",
    )


# ====================================================================
# Login — returns access in body, sets refresh cookie
# ====================================================================
class CookieTokenObtainPairView(TokenObtainPairView):
    authentication_classes = []  # no CSRF, no session auth
    permission_classes = []

    def post(self, request, *args, **kwargs):
        username = (request.data.get("username") or "")[:150]
        try:
            response = super().post(request, *args, **kwargs)
        except APIException:
            record_audit(
                actor=None,
                action="LOGIN_FAILURE",
                target_type="USER",
                target_repr=username,
                description=f"Failed login attempt: {username}",
                request=request,
            )
            raise

        if response.status_code == 200:
            refresh = response.data.pop("refresh", None)
            if refresh:
                _set_refresh_cookie(response, refresh)

            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.filter(username=username).first()
            profile = getattr(user, "profile", None) if user else None

            record_audit(
                actor=profile,
                action="LOGIN_SUCCESS",
                target_type="USER",
                target_repr=username,
                description=f"Successful login: {username}",
                request=request,
            )
        else:
            record_audit(
                actor=None,
                action="LOGIN_FAILURE",
                target_type="USER",
                target_repr=username,
                description=f"Failed login attempt: {username}",
                request=request,
            )

        return response


# ====================================================================
# Refresh — reads cookie, returns new access, rotates cookie
# ====================================================================
class CookieTokenRefreshView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=None,
        responses={
            200: AccessTokenResponseSerializer,
            401: OpenApiResponse(description="No refresh cookie, or it's invalid/expired."),
        },
        tags=["auth"],
        summary="Refresh the access token using the HttpOnly refresh cookie",
    )
    def post(self, request):
        raw = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if not raw:
            return Response(
                {"detail": "No refresh token present."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenRefreshSerializer(data={"refresh": raw})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            response = Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            _clear_refresh_cookie(response)
            return response

        access = serializer.validated_data["access"]
        new_refresh = serializer.validated_data.get("refresh")  # present when rotating

        response = Response({"access": access})
        if new_refresh:
            _set_refresh_cookie(response, new_refresh)
        return response


# ====================================================================
# Logout — blacklists the current refresh token, clears cookie
# ====================================================================
class CookieLogoutView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=None,
        responses={200: LogoutResponseSerializer},
        tags=["auth"],
        summary="Blacklist the refresh token and clear the refresh cookie",
    )
    def post(self, request):
        raw = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except TokenError:
                pass

        response = Response({"detail": "Logged out."})
        _clear_refresh_cookie(response)
        return response
