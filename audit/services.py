from audit.models import AuditLog


def get_client_ip(request) -> str | None:
    """Extract the real client IP, respecting X-Forwarded-For."""
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def record_audit(
    *,
    actor,
    action: str,
    target_type: str = "",
    target_id=None,
    target_repr: str = "",
    description: str = "",
    metadata: dict | None = None,
    request=None,
) -> AuditLog:
    """
    Create an audit log entry. Called from services and views.

    `actor` is a UserProfile or None (for unauthenticated events like
    login failures or system actions).
    """
    ip = get_client_ip(request)
    ua = ""
    if request is not None:
        ua = request.META.get("HTTP_USER_AGENT", "")[:500]

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_repr=target_repr[:255],
        description=description,
        metadata=metadata or {},
        ip_address=ip,
        user_agent=ua,
    )
