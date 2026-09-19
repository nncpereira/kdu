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
    roles = {"MAKER", "SUPERADMIN"}


class IsMakerOrSuperadmin(HasRole):
    roles = {"MAKER", "SUPERADMIN"}


class IsChecker(HasRole):
    roles = {"CHECKER", "SUPERADMIN"}


class IsCertifier(HasRole):
    roles = {"CERTIFIER", "SUPERADMIN"}


class IsCertifierOrSuperadmin(HasRole):
    roles = {"CERTIFIER", "SUPERADMIN"}


class IsSuperadmin(HasRole):
    roles = {"SUPERADMIN"}


class IsBoardOrChecker(HasRole):
    roles = {"BOARD", "CHECKER", "SUPERADMIN"}


class IsMemberViewer(HasRole):
    roles = {"MAKER", "BOARD", "CHECKER", "SUPERADMIN"}


class IsAuditor(HasRole):
    roles = {"AUDITOR"}


class IsMember(HasRole):
    roles = {"MEMBER"}


class IsStaffReadMembers(HasRole):
    """
    Roles allowed to read member records.
    Includes MAKER because the Teller needs to look up members
    to process deposits, withdrawals, and initial capital.
    """

    roles = {"MAKER", "BOARD", "CHECKER", "SUPERADMIN"}


class IsStaffReadSavings(HasRole):
    """
    Roles allowed to read savings transactions and balances.
    Includes MAKER because the Teller needs to look up history
    when processing a deposit or withdrawal.
    """

    roles = {"MAKER", "CHECKER", "CERTIFIER", "BOARD", "SUPERADMIN"}


class IsStaffReadLoans(HasRole):
    """
    Roles allowed to read loans and repayment history.
    Includes MAKER because the Loan Officer originates loans and
    processes repayments.
    """

    roles = {"MAKER", "CHECKER", "CERTIFIER", "BOARD", "SUPERADMIN"}


class IsStaffReadShu(HasRole):
    """
    Roles allowed to read SHU fiscal years, calculations, and payouts.
    Includes MAKER (they run the calculation) and CERTIFIER (they approve it).
    """

    roles = {"MAKER", "CHECKER", "CERTIFIER", "BOARD", "SUPERADMIN"}


class IsStaffReadExpenses(HasRole):
    """
    Roles allowed to read expense records.
    Includes MAKER because the administrator who records expenses
    needs to verify their entries.
    """

    roles = {"MAKER", "CHECKER", "CERTIFIER", "BOARD", "SUPERADMIN"}
