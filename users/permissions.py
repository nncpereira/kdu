from rest_framework.permissions import BasePermission

from users.models import UserProfile


class HasRole(BasePermission):
    """Base class — subclasses set `roles = {...}`."""

    roles = set()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        profile = getattr(user, "profile", None)
        return bool(profile and profile.role in self.roles)


class IsMaker(HasRole):
    roles = {UserProfile.Role.MAKER}


class IsChecker(HasRole):
    roles = {UserProfile.Role.CHECKER}


class IsCertifier(HasRole):
    roles = {UserProfile.Role.CERTIFIER}


class IsSuperadmin(HasRole):
    roles = {UserProfile.Role.SUPERADMIN}


class IsBoardOrChecker(HasRole):
    roles = {
        UserProfile.Role.BOARD,
        UserProfile.Role.CHECKER,
        UserProfile.Role.SUPERADMIN,
    }


class IsAuditor(HasRole):
    roles = {UserProfile.Role.AUDITOR}


class IsMember(HasRole):
    roles = {UserProfile.Role.MEMBER}
