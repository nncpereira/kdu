import csv
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Count, Sum, Q
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from audit.api.serializers import AuditLogSerializer, LedgerActivitySerializer
from audit.models import AuditLog
from audit.notifications import get_notifications_for
from core.permissions import IsBoardOrChecker, IsSuperadmin, IsAuditor, IsMaker
from ledger.models import JournalEntry


# ====================================================================
# Permission helper — audit access is Superadmin + Board + Auditor
# ====================================================================
class CanReadAudit(IsBoardOrChecker):
    """Extends board/checker access with the Auditor role."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        profile = getattr(user, "profile", None)
        return bool(
            profile and profile.role in {"SUPERADMIN", "BOARD", "AUDITOR", "CHECKER"}
        )


# ====================================================================
# Helpers
# ====================================================================
def _parse_filters(request):
    """
    Extract common filters from query params:
        start, end         — YYYY-MM-DD
        action             — exact match on action code
        actor              — user_id (UUID)
        target_type        — e.g. USER, MEMBER, CONFIG_CHANGE
    """
    filters = {}

    start = request.query_params.get("start")
    end = request.query_params.get("end")

    if start:
        filters["start"] = parse_date(start)
    if end:
        filters["end"] = parse_date(end)

    action = request.query_params.get("action")
    if action:
        filters["action"] = action

    actor = request.query_params.get("actor")
    if actor:
        filters["actor"] = actor

    target_type = request.query_params.get("target_type")
    if target_type:
        filters["target_type"] = target_type

    return filters


# ====================================================================
# Audit log
# ====================================================================
class AuditLogListView(APIView):
    permission_classes = [CanReadAudit]

    def get(self, request):
        filters = _parse_filters(request)
        qs = AuditLog.objects.select_related("actor__user").order_by("-created_at")

        if "start" in filters and filters["start"]:
            qs = qs.filter(created_at__date__gte=filters["start"])
        if "end" in filters and filters["end"]:
            qs = qs.filter(created_at__date__lte=filters["end"])
        if "action" in filters:
            qs = qs.filter(action=filters["action"])
        if "actor" in filters:
            qs = qs.filter(actor_id=filters["actor"])
        if "target_type" in filters:
            qs = qs.filter(target_type=filters["target_type"])

        # Cap at 500 for the UI; export handles larger ranges.
        limit = min(int(request.query_params.get("limit", 200)), 500)
        total = qs.count()
        rows = qs[:limit]

        return Response(
            {
                "count": total,
                "limit": limit,
                "results": AuditLogSerializer(rows, many=True).data,
            }
        )


class AuditLogDetailView(APIView):
    permission_classes = [CanReadAudit]

    def get(self, request, pk):
        entry = AuditLog.objects.select_related("actor__user").get(pk=pk)
        return Response(AuditLogSerializer(entry).data)


class AuditLogExportView(APIView):
    """
    Streaming CSV export for auditors. Same filters as the list view.
    """

    permission_classes = [CanReadAudit]

    def get(self, request):
        filters = _parse_filters(request)
        qs = AuditLog.objects.select_related("actor__user").order_by("-created_at")

        if "start" in filters and filters["start"]:
            qs = qs.filter(created_at__date__gte=filters["start"])
        if "end" in filters and filters["end"]:
            qs = qs.filter(created_at__date__lte=filters["end"])
        if "action" in filters:
            qs = qs.filter(action=filters["action"])
        if "actor" in filters:
            qs = qs.filter(actor_id=filters["actor"])
        if "target_type" in filters:
            qs = qs.filter(target_type=filters["target_type"])

        response = HttpResponse(content_type="text/csv")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response["Content-Disposition"] = (
            f'attachment; filename="audit-log-{stamp}.csv"'
        )

        writer = csv.writer(response)
        writer.writerow(
            [
                "Timestamp",
                "Actor",
                "Role",
                "Action",
                "Target Type",
                "Target",
                "Description",
                "IP Address",
            ]
        )

        for entry in qs.iterator():
            writer.writerow(
                [
                    entry.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    entry.actor.user.username if entry.actor else "system",
                    entry.actor.role if entry.actor else "",
                    entry.action,
                    entry.target_type,
                    entry.target_repr,
                    entry.description,
                    entry.ip_address or "",
                ]
            )

        return response


# ====================================================================
# Ledger activity (JournalEntry aggregator)
# ====================================================================
class LedgerActivityListView(APIView):
    permission_classes = [CanReadAudit]

    def get(self, request):
        filters = _parse_filters(request)
        qs = (
            JournalEntry.objects.select_related(
                "created_by__user", "certified_by__user"
            )
            .annotate(
                line_count=Count("lines"),
                total_amount=Sum("lines__amount"),
            )
            .order_by("-created_at")
        )

        if "start" in filters and filters["start"]:
            qs = qs.filter(entry_date__gte=filters["start"])
        if "end" in filters and filters["end"]:
            qs = qs.filter(entry_date__lte=filters["end"])

        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        only_reversals = request.query_params.get("reversals_only")
        if only_reversals == "1":
            qs = qs.filter(original_journal_entry__isnull=False)

        limit = min(int(request.query_params.get("limit", 200)), 500)
        total = qs.count()
        rows = qs[:limit]

        data = [
            {
                "id": str(e.id),
                "entry_date": e.entry_date,
                "description": e.description,
                "maker_username": (
                    e.created_by.user.username if e.created_by else None
                ),
                "certifier_username": (
                    e.certified_by.user.username if e.certified_by else None
                ),
                "status": e.status,
                "line_count": e.line_count,
                "total_amount": e.total_amount or Decimal("0.00"),
                "is_reversal": e.original_journal_entry_id is not None,
                "created_at": e.created_at,
            }
            for e in rows
        ]

        return Response(
            {
                "count": total,
                "limit": limit,
                "results": LedgerActivitySerializer(data, many=True).data,
            }
        )


# ====================================================================
# NOTIFICATIONS
# ====================================================================
class NotificationsView(APIView):
    """
    Return the current user's actionable notifications.
    Accessible to any authenticated staff user; members get an empty list.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, "profile", None)
        if not profile or profile.role == "MEMBER":
            return Response({"count": 0, "items": []})

        items = get_notifications_for(profile)
        return Response(
            {
                "count": len(items),
                "items": items,
            }
        )
