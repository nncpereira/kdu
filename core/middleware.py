from django.http import Http404

ADMIN_PREFIX = "/admin/"


class RestrictDjangoAdminMiddleware:
    """
    Gate /admin/ behind SUPERADMIN + an established Django session.

    Django admin has no login page of its own here — visiting /admin/
    directly (authenticated or not) 404s. A session is only granted via
    users.api.views.AdminSessionGrantView, which requires a valid JWT for
    a SUPERADMIN (see AppLayout's "Django Admin" link on the frontend).
    This avoids leaking the admin's existence to anyone who isn't already
    a signed-in superadmin.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(ADMIN_PREFIX):
            user = request.user
            profile = getattr(user, "profile", None)
            is_superadmin = (
                user.is_authenticated and profile and profile.role == "SUPERADMIN"
            )
            if not is_superadmin:
                raise Http404()
        return self.get_response(request)
