from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ok", "degraded"])
    database = serializers.CharField()
    version = serializers.CharField()


@extend_schema(
    responses={200: HealthCheckSerializer},
    tags=["core"],
    summary="Service health check",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    db_ok = "ok"
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except Exception as e:
        db_ok = f"error: {e}"

    return Response(
        {
            "status": "ok" if db_ok == "ok" else "degraded",
            "database": db_ok,
            "version": "1.0.0",
        }
    )
