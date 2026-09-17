from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    """Base class — subclasses set `roles`."""
    roles: set = set()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        profile = getattr(user, "profile", None)
        return bool(profile and profile.role in self.roles)


class IsMaker(HasRole):
    roles = {"MAKER"}


class IsChecker(HasRole):
    roles = {"CHECKER"}


class IsCertifier(HasRole):
    roles = {"CERTIFIER"}


class IsSuperadmin(HasRole):
    roles = {"SUPERADMIN"}


class IsBoardOrChecker(HasRole):
    roles = {"BOARD", "CHECKER", "SUPERADMIN"}


class IsAuditor(HasRole):
    roles = {"AUDITOR"}


class IsMember(HasRole):
    roles = {"MEMBER"}
