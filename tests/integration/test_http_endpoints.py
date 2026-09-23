"""
HTTP integration tests for the KDU API.

Verifies:
    - JWT auth flow (obtain / refresh / verify)
    - Role-based permission enforcement (Maker / Checker / Certifier / Board)
    - Full Maker-Checker-Certifier pipeline over HTTP
    - Serializer shapes and error responses
    - Endpoint routing for every app

Run with:
    pytest tests/integration/test_http_endpoints.py -v

Run a single class:
    pytest tests/integration/test_http_endpoints.py::TestSavingsHTTP -v
"""

from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from expenses.models import Expense
from governance.models import GlobalConfig, GlobalConfigChange
from loans.models import Loan, LoanRepayment
from members.models import Member
from shu.models import ShuCalculation
from tests.factories import ShuFiscalYearFactory, ShuWeightingBaseFactory

pytestmark = [pytest.mark.integration, pytest.mark.http]


# ====================================================================
# Helpers
# ====================================================================
def _get_jwt(client: APIClient, username: str, password: str = "testpass123") -> str:
    resp = client.post(
        "/api/v1/auth/token/",
        {"username": username, "password": password},
        format="json",
    )
    assert resp.status_code == 200, f"JWT obtain failed: {resp.content}"
    return resp.data["access"]


@pytest.fixture
def api_for(db):
    """
    Factory fixture.
    Usage:  client = api_for(maker)
            resp = client.get("/api/v1/...")
    """

    def _make(profile):
        client = APIClient()
        token = _get_jwt(client, profile.user.username)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    return _make


def _run_pipeline(checker_client, certifier_client, actor_id):
    """Run check + certify via HTTP and assert both succeed."""
    r1 = checker_client.post(f"/api/v1/pipeline/{actor_id}/check/", format="json")
    assert r1.status_code == 200, f"Check failed: {r1.content}"

    r2 = certifier_client.post(f"/api/v1/pipeline/{actor_id}/certify/", format="json")
    assert r2.status_code == 200, f"Certify failed: {r2.content}"


# ====================================================================
# Health
# ====================================================================
class TestHealth:
    def test_health_ok(self, db):
        client = APIClient()
        resp = client.get("/health/")
        assert resp.status_code == 200
        assert resp.data["status"] == "ok"
        assert resp.data["database"] == "ok"


# ====================================================================
# Auth
# ====================================================================
class TestAuthHTTP:

    def test_obtain_token_success(self, db, maker):
        client = APIClient()
        resp = client.post(
            "/api/v1/auth/token/",
            {"username": maker.user.username, "password": "testpass123"},
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" not in resp.data  # ← refresh no longer in body
        # Refresh token is now in a cookie.
        assert "kdu_refresh" in resp.cookies

    def test_obtain_token_bad_password(self, db, maker):
        client = APIClient()
        resp = client.post(
            "/api/v1/auth/token/",
            {"username": maker.user.username, "password": "wrong"},
            format="json",
        )
        assert resp.status_code == 401

    def test_refresh_token(self, db, maker):
        client = APIClient()
        # Login — cookie is captured by the test client automatically.
        r1 = client.post(
            "/api/v1/auth/token/",
            {"username": maker.user.username, "password": "testpass123"},
            format="json",
        )
        assert r1.status_code == 200

        # Refresh — the test client sends the cookie along.
        r2 = client.post("/api/v1/auth/token/refresh/", {}, format="json")
        assert r2.status_code == 200
        assert "access" in r2.data

    def test_verify_token(self, db, maker):
        client = APIClient()
        r1 = client.post(
            "/api/v1/auth/token/",
            {"username": maker.user.username, "password": "testpass123"},
            format="json",
        )
        access = r1.data["access"]

        r2 = client.post(
            "/api/v1/auth/token/verify/",
            {"token": access},
            format="json",
        )
        assert r2.status_code == 200

    def test_unauthenticated_returns_401(self, db):
        client = APIClient()
        resp = client.get("/api/v1/users/me/")
        assert resp.status_code == 401

    def test_refresh_without_cookie_fails(self, db):
        client = APIClient()
        resp = client.post("/api/v1/auth/token/refresh/", {}, format="json")
        assert resp.status_code == 401

    def test_logout_blacklists_refresh(self, db, maker):
        client = APIClient()
        client.post(
            "/api/v1/auth/token/",
            {"username": maker.user.username, "password": "testpass123"},
            format="json",
        )
        # Logout
        r = client.post("/api/v1/auth/logout/", {}, format="json")
        assert r.status_code == 200

        # Cookie should be cleared; a subsequent refresh fails.
        r2 = client.post("/api/v1/auth/token/refresh/", {}, format="json")
        assert r2.status_code == 401


# ====================================================================
# Users / me
# ====================================================================
class TestUsersHTTP:
    def test_get_me(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.get("/api/v1/users/me/")
        assert resp.status_code == 200
        assert resp.data["username"] == maker.user.username
        assert resp.data["role"] == "MAKER"
        assert resp.data["must_change_password"] is False

    def test_change_password_success(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.post(
            "/api/v1/users/me/change-password/",
            {"old_password": "testpass123", "new_password": "NewPass!2026"},
            format="json",
        )
        assert resp.status_code == 200
        assert "detail" in resp.data

    def test_change_password_wrong_old(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.post(
            "/api/v1/users/me/change-password/",
            {"old_password": "nope", "new_password": "NewPass!2026"},
            format="json",
        )
        assert resp.status_code == 400

    def test_update_my_profile(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.patch(
            "/api/v1/users/me/",
            {
                "first_name": "NewFirst",
                "last_name": "NewLast",
                "email": "newmaker@example.com",
            },
            format="json",
        )
        assert resp.status_code == 200, resp.content
        assert resp.data["first_name"] == "NewFirst"
        assert resp.data["last_name"] == "NewLast"
        assert resp.data["email"] == "newmaker@example.com"

        # Confirm it persisted
        r2 = client.get("/api/v1/users/me/")
        assert r2.data["first_name"] == "NewFirst"

    def test_update_my_profile_partial(self, db, api_for, maker):
        """Only send the fields you want to change."""
        client = api_for(maker)
        resp = client.patch(
            "/api/v1/users/me/",
            {"first_name": "OnlyFirst"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["first_name"] == "OnlyFirst"

    def test_cannot_change_role_via_profile(self, db, api_for, maker):
        """Role is read-only on the self endpoint."""
        client = api_for(maker)
        resp = client.patch(
            "/api/v1/users/me/",
            {"role": "SUPERADMIN"},
            format="json",
        )
        # Ignored silently — role remains MAKER
        assert resp.status_code == 200
        assert resp.data["role"] == "MAKER"


class TestUsersAdminHTTP:
    def test_superadmin_lists_staff(self, db, api_for, superadmin, maker, checker):
        client = api_for(superadmin)
        resp = client.get("/api/v1/users/")
        assert resp.status_code == 200
        usernames = {u["username"] for u in resp.data}
        assert maker.user.username in usernames
        assert checker.user.username in usernames

    def test_maker_cannot_list_staff(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.get("/api/v1/users/")
        assert resp.status_code == 403

    def test_checker_cannot_list_staff(self, db, api_for, checker):
        client = api_for(checker)
        resp = client.get("/api/v1/users/")
        assert resp.status_code == 403

    def test_superadmin_creates_staff(self, db, api_for, superadmin):
        client = api_for(superadmin)
        resp = client.post(
            "/api/v1/users/",
            {
                "username": "newmaker",
                "password": "FreshPass2026!",
                "role": "MAKER",
                "email": "newmaker@example.com",
                "first_name": "New",
                "last_name": "Maker",
            },
            format="json",
        )
        assert resp.status_code == 201, resp.content
        assert resp.data["username"] == "newmaker"
        assert resp.data["role"] == "MAKER"
        assert resp.data["must_change_password"] is True

    def test_cannot_create_duplicate_username(self, db, api_for, superadmin, maker):
        client = api_for(superadmin)
        resp = client.post(
            "/api/v1/users/",
            {
                "username": maker.user.username,
                "password": "FreshPass2026!",
                "role": "MAKER",
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_cannot_create_member_role_via_admin(self, db, api_for, superadmin):
        client = api_for(superadmin)
        resp = client.post(
            "/api/v1/users/",
            {
                "username": "badmember",
                "password": "FreshPass2026!",
                "role": "MEMBER",
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_superadmin_disables_staff(self, db, api_for, superadmin, maker):
        client = api_for(superadmin)
        resp = client.post(f"/api/v1/users/{maker.id}/disable/", format="json")
        assert resp.status_code == 200
        assert resp.data["is_active"] is False

    def test_cannot_disable_self(self, db, api_for, superadmin):
        client = api_for(superadmin)
        resp = client.post(f"/api/v1/users/{superadmin.id}/disable/", format="json")
        assert resp.status_code == 400

    def test_superadmin_resets_password(self, db, api_for, superadmin, maker):
        client = api_for(superadmin)
        resp = client.post(f"/api/v1/users/{maker.id}/reset-password/", format="json")
        assert resp.status_code == 200
        assert "temporary_password" in resp.data
        assert len(resp.data["temporary_password"]) > 0

    def test_update_staff_name(self, db, api_for, superadmin, maker):
        client = api_for(superadmin)
        resp = client.patch(
            f"/api/v1/users/{maker.id}/",
            {"first_name": "Renamed", "last_name": "Person"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["first_name"] == "Renamed"
        assert resp.data["last_name"] == "Person"


# ====================================================================
# Permission enforcement
# ====================================================================
class TestPermissionsHTTP:

    def test_maker_can_list_members(self, db, api_for, maker):
        """Teller (MAKER) needs to see member records to process deposits
        and to navigate to a member to pay initial capital."""
        client = api_for(maker)
        resp = client.get("/api/v1/members/")
        assert resp.status_code == 200

    def test_maker_can_view_member_detail(self, db, api_for, maker, maria):
        client = api_for(maker)
        resp = client.get(f"/api/v1/members/{maria.id}/")
        assert resp.status_code == 200
        assert resp.data["id"] == str(maria.id)

    def test_checker_can_list_members(self, db, api_for, checker):
        client = api_for(checker)
        resp = client.get("/api/v1/members/")
        assert resp.status_code == 200

    def test_board_can_list_members(self, db, api_for, board):
        client = api_for(board)
        resp = client.get("/api/v1/members/")
        assert resp.status_code == 200

    def test_maker_cannot_check_pipeline(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.get("/api/v1/pipeline/pending-check/")
        assert resp.status_code == 403

    def test_checker_cannot_access_certify_queue(self, db, api_for, checker):
        client = api_for(checker)
        resp = client.get("/api/v1/pipeline/pending-certify/")
        assert resp.status_code == 403

    def test_certifier_can_access_certify_queue(self, db, api_for, certifier):
        client = api_for(certifier)
        resp = client.get("/api/v1/pipeline/pending-certify/")
        assert resp.status_code == 200

    def test_superadmin_can_access_both_queues(self, db, api_for, superadmin):
        client = api_for(superadmin)
        r1 = client.get("/api/v1/pipeline/pending-check/")
        r2 = client.get("/api/v1/pipeline/pending-certify/")
        assert r1.status_code == 200
        assert r2.status_code == 200


# ====================================================================
# Members
# ====================================================================
class TestMembersHTTP:
    def test_maker_can_create_member(self, db, api_for, maker):
        client = api_for(maker)
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "salutation": "Mr",
            "phone_number": "77000111",
            "date_of_birth": "1985-06-15",
            "aldeia": "A",
            "suco": "S",
            "posto": "P",
            "municipio": "Dili",
            "profession": "Farmer",
        }
        resp = client.post("/api/v1/members/", payload, format="json")
        assert resp.status_code == 201, resp.content
        assert resp.data["status"] == "Pending"
        assert resp.data["kapital_sosial_balance"] == "0.00"
        assert resp.data["membership_number"].startswith("KDU-")

    def test_list_members_paginated(self, db, api_for, checker, maria):
        client = api_for(checker)
        resp = client.get("/api/v1/members/")
        assert resp.status_code == 200
        assert "count" in resp.data
        assert "results" in resp.data
        assert resp.data["count"] >= 1

    def test_filter_members_by_status(self, db, api_for, checker, maria):
        client = api_for(checker)
        resp = client.get("/api/v1/members/?status=Active")
        assert resp.status_code == 200
        for member in resp.data["results"]:
            assert member["status"] == "Active"

    def test_get_member_detail(self, db, api_for, checker, maria):
        client = api_for(checker)
        resp = client.get(f"/api/v1/members/{maria.id}/")
        assert resp.status_code == 200
        assert resp.data["id"] == str(maria.id)

    def test_get_member_404(self, db, api_for, checker):
        client = api_for(checker)
        resp = client.get("/api/v1/members/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == 404

    def test_pay_initial_capital_below_minimum(self, db, api_for, maker):
        client = api_for(maker)
        # Create a fresh pending member
        r = client.post(
            "/api/v1/members/",
            {
                "first_name": "Low",
                "last_name": "Cap",
                "phone_number": "77000222",
                "date_of_birth": "1990-01-01",
            },
            format="json",
        )
        member_id = r.data["id"]

        resp = client.post(
            f"/api/v1/members/{member_id}/initial-capital/",
            {"amount": "40.00"},
            format="json",
        )
        assert resp.status_code == 400

    def test_pay_initial_capital_and_run_pipeline(
        self, db, api_for, maker, checker, certifier
    ):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        r = maker_c.post(
            "/api/v1/members/",
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "phone_number": "77000333",
                "date_of_birth": "1990-01-01",
            },
            format="json",
        )
        member_id = r.data["id"]

        r2 = maker_c.post(
            f"/api/v1/members/{member_id}/initial-capital/",
            {"amount": "50.00"},
            format="json",
        )
        assert r2.status_code == 201, r2.content
        actor_id = r2.data["pipeline_actor_id"]

        _run_pipeline(checker_c, certifier_c, actor_id)

        # Verify the member was activated
        m = Member.objects.get(id=member_id)
        assert m.status == "Active"
        assert m.kapital_sosial_balance == Decimal("50.00")

        # The initial capital payment shows up in the member's capital
        # history, even though it's not a savings.Transaction.
        history = maker_c.get(f"/api/v1/members/{member_id}/capital-history/")
        assert history.status_code == 200
        assert history.data["exit_requests"] == []
        assert len(history.data["onboardings"]) == 1
        onboarding = history.data["onboardings"][0]
        assert onboarding["status"] == "COMPLETED"
        assert onboarding["initial_capital_amount"] == "50.00"

    def test_capital_history_empty_for_new_member(self, db, api_for, maker):
        maker_c = api_for(maker)
        r = maker_c.post(
            "/api/v1/members/",
            {
                "first_name": "New",
                "last_name": "Member",
                "phone_number": "77000444",
                "date_of_birth": "1990-01-01",
            },
            format="json",
        )
        member_id = r.data["id"]

        resp = maker_c.get(f"/api/v1/members/{member_id}/capital-history/")
        assert resp.status_code == 200
        assert resp.data == {
            "onboardings": [],
            "exit_requests": [],
            "loan_repayment_sweeps": [],
        }

# ====================================================================
# Members Self-Service Portal
# ====================================================================
class TestMemberPortalHTTP:
    @pytest.fixture
    def member_user(self, db, maria):
        """
        Create a Django auth user with role=MEMBER and link it to Maria.
        Returns (user_profile, maria).
        """
        from django.contrib.auth import get_user_model

        from users.models import UserProfile

        User = get_user_model()
        user = User.objects.create_user(
            username=maria.membership_number,
            password="memberpass123",
        )
        profile = UserProfile.objects.create(
            user=user,
            role=UserProfile.Role.MEMBER,
        )
        maria.user = user
        maria.save(update_fields=["user"])
        return profile

    @pytest.fixture
    def member_client(self, member_user):
        client = APIClient()
        token = _get_jwt(client, member_user.user.username, "memberpass123")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    def test_member_can_fetch_dashboard(self, db, member_client):
        resp = member_client.get("/api/v1/members/me/dashboard/")
        assert resp.status_code == 200
        assert "member" in resp.data
        assert "capital" in resp.data
        assert "voluntary" in resp.data
        assert "loans" in resp.data
        assert "recent_activity" in resp.data

    def test_member_can_fetch_profile(self, db, member_client, maria):
        resp = member_client.get("/api/v1/members/me/")
        assert resp.status_code == 200
        assert resp.data["membership_number"] == maria.membership_number

    def test_member_can_update_own_contact_details(self, db, member_client):
        resp = member_client.patch(
            "/api/v1/members/me/",
            {"phone_number": "77009999", "profession": "Trader"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["phone_number"] == "77009999"
        assert resp.data["profession"] == "Trader"

    def test_member_cannot_edit_name(self, db, member_client):
        """first_name is not in the editable serializer — silently ignored."""
        resp = member_client.patch(
            "/api/v1/members/me/",
            {"first_name": "Hacked"},
            format="json",
        )
        assert resp.status_code == 200
        # The name didn't change.
        assert resp.data["first_name"] != "Hacked"

    def test_member_can_fetch_savings(self, db, member_client):
        resp = member_client.get("/api/v1/members/me/savings/")
        assert resp.status_code == 200
        assert "kapital_sosial_balance" in resp.data
        assert "voluntary" in resp.data

    def test_member_can_fetch_transactions(self, db, member_client):
        resp = member_client.get("/api/v1/members/me/transactions/")
        assert resp.status_code == 200
        assert isinstance(resp.data, list)

    def test_member_can_fetch_loans(self, db, member_client):
        resp = member_client.get("/api/v1/members/me/loans/")
        assert resp.status_code == 200
        assert isinstance(resp.data, list)

    def test_member_can_fetch_shu_statement(self, db, member_client):
        resp = member_client.get("/api/v1/members/me/shu/")
        assert resp.status_code == 200
        assert isinstance(resp.data, list)

    def test_maker_cannot_use_me_endpoints(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.get("/api/v1/members/me/dashboard/")
        assert resp.status_code == 403

    def test_member_cannot_use_staff_member_list(self, db, member_client):
        resp = member_client.get("/api/v1/members/")
        assert resp.status_code == 403


class TestMemberLoginManagementHTTP:
    def test_superadmin_creates_login(self, db, api_for, superadmin, maria):
        # Ensure she has no login yet
        maria.user = None
        maria.save(update_fields=["user"])

        client = api_for(superadmin)
        resp = client.post(
            f"/api/v1/members/{maria.id}/create-login/",
            format="json",
        )
        assert resp.status_code == 201, resp.content
        assert resp.data["login_username"] == maria.membership_number
        assert "temporary_password" in resp.data
        assert len(resp.data["temporary_password"]) > 0

        # Confirm the link is now set
        maria.refresh_from_db()
        assert maria.user_id is not None
        assert maria.user.username == maria.membership_number

    def test_cannot_create_duplicate_login(self, db, api_for, superadmin, maria):
        from django.contrib.auth import get_user_model

        from users.models import UserProfile

        User = get_user_model()
        user = User.objects.create_user(username="KDU-000001", password="x")
        UserProfile.objects.create(user=user, role="MEMBER")
        maria.user = user
        maria.save(update_fields=["user"])

        client = api_for(superadmin)
        resp = client.post(
            f"/api/v1/members/{maria.id}/create-login/",
            format="json",
        )
        assert resp.status_code == 400
        assert "already has a login" in resp.data["detail"]

    def test_maker_cannot_create_login(self, db, api_for, maker, maria):
        client = api_for(maker)
        resp = client.post(
            f"/api/v1/members/{maria.id}/create-login/",
            format="json",
        )
        assert resp.status_code == 403

    def test_superadmin_resets_member_password(self, db, api_for, superadmin, maria):
        from django.contrib.auth import get_user_model

        from users.models import UserProfile

        User = get_user_model()
        user = User.objects.create_user(username="KDU-000001", password="oldpass123")
        UserProfile.objects.create(user=user, role="MEMBER")
        maria.user = user
        maria.save(update_fields=["user"])

        client = api_for(superadmin)
        resp = client.post(
            f"/api/v1/members/{maria.id}/reset-login-password/",
            format="json",
        )
        assert resp.status_code == 200
        assert "temporary_password" in resp.data

    def test_serializer_exposes_login_status(self, db, api_for, board, maria):
        from django.contrib.auth import get_user_model

        from users.models import UserProfile

        User = get_user_model()
        user = User.objects.create_user(username="KDU-000001", password="x")
        UserProfile.objects.create(user=user, role="MEMBER")
        maria.user = user
        maria.save(update_fields=["user"])

        client = api_for(board)
        resp = client.get(f"/api/v1/members/{maria.id}/")
        assert resp.status_code == 200
        assert resp.data["has_login"] is True
        assert resp.data["login_username"] == "KDU-000001"


# ====================================================================
# Savings
# ====================================================================
class TestSavingsHTTP:
    def test_deposit_full_flow(self, db, api_for, maker, checker, certifier, maria):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        resp = maker_c.post(
            "/api/v1/savings/deposit/",
            {"member": str(maria.id), "amount": "1000.00"},
            format="json",
        )
        assert resp.status_code == 201, resp.content
        assert resp.data["obligatory_portion"] == "20.00"
        assert resp.data["voluntary_portion"] == "980.00"
        assert resp.data["status"] == "PENDING_CHECK"

        _run_pipeline(checker_c, certifier_c, resp.data["pipeline_actor"])

        maria.refresh_from_db()
        assert maria.kapital_sosial_balance == Decimal("70.00")
        assert maria.voluntary_deposit.balance_available == Decimal("980.00")

    def test_withdraw_full_flow(self, db, api_for, maker, checker, certifier, maria):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        # Fund first — first deposit of month splits 20 / 480
        r = maker_c.post(
            "/api/v1/savings/deposit/",
            {"member": str(maria.id), "amount": "500.00"},
            format="json",
        )
        assert r.status_code == 201
        assert r.data["obligatory_portion"] == "20.00"
        assert r.data["voluntary_portion"] == "480.00"
        _run_pipeline(checker_c, certifier_c, r.data["pipeline_actor"])

        # Verify voluntary balance after deposit
        maria.refresh_from_db()
        assert maria.voluntary_deposit.balance_available == Decimal("480.00")

        # Now withdraw
        w = maker_c.post(
            "/api/v1/savings/withdraw/",
            {"member": str(maria.id), "amount": "200.00"},
            format="json",
        )
        assert w.status_code == 201, w.content

        _run_pipeline(checker_c, certifier_c, w.data["pipeline_actor"])

        maria.refresh_from_db()
        # Deposit: 500 = 20 obligatory + 480 voluntary (first deposit of month)
        # Withdraw 200 from voluntary → 280 remains
        assert maria.voluntary_deposit.balance_available == Decimal("280.00")
        assert maria.voluntary_deposit.balance_held_pipeline == Decimal("0.00")

    def test_withdraw_insufficient_funds(self, db, api_for, maker, maria):
        client = api_for(maker)
        resp = client.post(
            "/api/v1/savings/withdraw/",
            {"member": str(maria.id), "amount": "5000.00"},
            format="json",
        )
        assert resp.status_code == 400

    def test_list_transactions(
        self, db, api_for, board, maker, checker, certifier, maria
    ):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        r = maker_c.post(
            "/api/v1/savings/deposit/",
            {"member": str(maria.id), "amount": "100.00"},
            format="json",
        )
        _run_pipeline(checker_c, certifier_c, r.data["pipeline_actor"])

        board_c = api_for(board)
        resp = board_c.get("/api/v1/savings/transactions/")
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_get_voluntary_balance(self, db, api_for, board, maria):
        # Ensure a voluntary row exists
        from savings.models import MemberVoluntaryDeposit

        MemberVoluntaryDeposit.objects.get_or_create(member=maria)

        client = api_for(board)
        resp = client.get(f"/api/v1/savings/members/{maria.id}/voluntary/")
        assert resp.status_code == 200
        assert "balance_available" in resp.data
        assert "balance_held_pipeline" in resp.data

    def test_voluntary_balance_returns_zeros_when_no_row(self, db, api_for, board):
        from members.models import Member

        m = Member.objects.create(
            first_name="Fresh",
            last_name="Member",
            phone_number="77000999",
            date_of_birth="1990-01-01",
            status="Pending",
        )
        client = api_for(board)
        resp = client.get(f"/api/v1/savings/members/{m.id}/voluntary/")
        assert resp.status_code == 200
        assert resp.data["balance_available"] == "0.00"
        assert resp.data["balance_held_pipeline"] == "0.00"

    def test_maker_can_list_transactions(self, db, api_for, maker):
        """Teller needs to look up member savings history."""
        client = api_for(maker)
        resp = client.get("/api/v1/savings/transactions/")
        assert resp.status_code == 200

    def test_certifier_can_list_transactions(self, db, api_for, certifier):
        client = api_for(certifier)
        resp = client.get("/api/v1/savings/transactions/")
        assert resp.status_code == 200


# ====================================================================
# Loans
# ====================================================================
class TestLoansHTTP:
    def _disburse(self, maker_c, checker_c, certifier_c, maria):
        r = maker_c.post(
            "/api/v1/loans/",
            {
                "member": str(maria.id),
                "principal": "9000.00",
                "term_months": 12,
                "monthly_rate": "0.0200",
                "purpose": "working capital",
            },
            format="json",
        )
        assert r.status_code == 201, r.content
        loan_id = r.data["id"]

        loan = Loan.objects.get(id=loan_id)
        actor_id = str(loan.pipeline_actor_id)
        _run_pipeline(checker_c, certifier_c, actor_id)
        return loan_id

    def test_originate_and_disburse(
        self, db, api_for, maker, checker, certifier, maria
    ):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        loan_id = self._disburse(maker_c, checker_c, certifier_c, maria)

        loan = Loan.objects.get(id=loan_id)
        assert loan.status == "DISBURSED"
        assert loan.principal_outstanding == Decimal("9000.00")

    def test_list_loans(self, db, api_for, board, maker, checker, certifier, maria):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)
        self._disburse(maker_c, checker_c, certifier_c, maria)

        board_c = api_for(board)
        resp = board_c.get("/api/v1/loans/")
        assert resp.status_code == 200
        assert resp.data["count"] >= 1

    def test_manual_repayment_full_flow(
        self, db, api_for, maker, checker, certifier, maria
    ):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        loan_id = self._disburse(maker_c, checker_c, certifier_c, maria)

        r = maker_c.post(
            f"/api/v1/loans/{loan_id}/repay/manual/",
            {"principal_paid": "500.00", "interest_paid": "90.00"},
            format="json",
        )
        assert r.status_code == 201, r.content
        repayment_id = r.data["id"]

        repayment = LoanRepayment.objects.get(id=repayment_id)
        _run_pipeline(checker_c, certifier_c, str(repayment.pipeline_actor_id))

        loan = Loan.objects.get(id=loan_id)
        assert loan.principal_outstanding == Decimal("8500.00")

    def test_scheduled_repayment_waterfall(
        self, db, api_for, maker, checker, certifier, maria
    ):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        loan_id = self._disburse(maker_c, checker_c, certifier_c, maria)

        r = maker_c.post(
            f"/api/v1/loans/{loan_id}/repay/scheduled/",
            {"cash_amount": "1000.00", "scheduled_principal": "700.00"},
            format="json",
        )
        assert r.status_code == 201, r.content
        repayment_id = r.data["id"]

        repayment = LoanRepayment.objects.get(id=repayment_id)
        _run_pipeline(checker_c, certifier_c, str(repayment.pipeline_actor_id))

        loan = Loan.objects.get(id=loan_id)
        # 9000 - 700 = 8300
        assert loan.principal_outstanding == Decimal("8300.00")

        # Cash beyond interest (180) + scheduled principal (700) = 120
        # left over, which the waterfall sweeps into the member's own
        # savings: 20 to the obligatory cap, the rest (100) voluntary.
        repayment.refresh_from_db()
        assert repayment.obligatory_portion == Decimal("20.00")
        assert repayment.voluntary_portion == Decimal("100.00")

        # And it shows up in the member's transaction/capital history.
        history = maker_c.get(f"/api/v1/members/{maria.id}/capital-history/")
        assert history.status_code == 200
        sweeps = history.data["loan_repayment_sweeps"]
        assert len(sweeps) == 1
        assert sweeps[0]["obligatory_portion"] == "20.00"
        assert sweeps[0]["voluntary_portion"] == "100.00"

    def test_scheduled_insufficient_for_interest(
        self, db, api_for, maker, checker, certifier, maria
    ):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        loan_id = self._disburse(maker_c, checker_c, certifier_c, maria)

        r = maker_c.post(
            f"/api/v1/loans/{loan_id}/repay/scheduled/",
            {"cash_amount": "50.00", "scheduled_principal": "700.00"},
            format="json",
        )
        # Interest due = 180.00 so 50 < 180 → rejected
        assert r.status_code == 400

    def test_list_repayments(
        self, db, api_for, maker, checker, certifier, board, maria
    ):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        loan_id = self._disburse(maker_c, checker_c, certifier_c, maria)

        # Make a repayment
        r = maker_c.post(
            f"/api/v1/loans/{loan_id}/repay/manual/",
            {"principal_paid": "100.00", "interest_paid": "50.00"},
            format="json",
        )
        repayment = LoanRepayment.objects.get(id=r.data["id"])
        _run_pipeline(checker_c, certifier_c, str(repayment.pipeline_actor_id))

        board_c = api_for(board)
        resp = board_c.get(f"/api/v1/loans/{loan_id}/repayments/")
        assert resp.status_code == 200
        assert len(resp.data) == 1

    def test_maker_can_list_loans(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.get("/api/v1/loans/")
        assert resp.status_code == 200

    def test_certifier_can_list_loans(self, db, api_for, certifier):
        client = api_for(certifier)
        resp = client.get("/api/v1/loans/")
        assert resp.status_code == 200

    def test_maker_can_view_loan_detail(
        self, db, api_for, maker, checker, certifier, maria
    ):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        loan_id = self._disburse(maker_c, checker_c, certifier_c, maria)
        resp = maker_c.get(f"/api/v1/loans/{loan_id}/")
        assert resp.status_code == 200
        assert resp.data["id"] == loan_id


# ====================================================================
# Expenses
# ====================================================================
class TestExpensesHTTP:
    def test_record_and_list(self, db, api_for, maker, checker, certifier, board):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        r = maker_c.post(
            "/api/v1/expenses/",
            {
                "description": "AGM venue",
                "amount": "500.00",
                "expense_account_code": "5101",
                "payment_date": "2026-06-30",
            },
            format="json",
        )
        assert r.status_code == 201, r.content

        expense = Expense.objects.get(id=r.data["id"])
        _run_pipeline(checker_c, certifier_c, str(expense.pipeline_actor_id))

        board_c = api_for(board)
        resp = board_c.get("/api/v1/expenses/")
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_non_expense_account_rejected(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.post(
            "/api/v1/expenses/",
            {
                "description": "bad",
                "amount": "100.00",
                "expense_account_code": "1001",  # Asset
                "payment_date": "2026-06-30",
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_expense_detail(self, db, api_for, maker, board):
        maker_c = api_for(maker)
        r = maker_c.post(
            "/api/v1/expenses/",
            {
                "description": "Utilities",
                "amount": "150.00",
                "expense_account_code": "5103",
                "payment_date": "2026-06-30",
            },
            format="json",
        )
        expense_id = r.data["id"]

        board_c = api_for(board)
        resp = board_c.get(f"/api/v1/expenses/{expense_id}/")
        assert resp.status_code == 200
        assert resp.data["id"] == expense_id

    def test_maker_can_list_expenses(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.get("/api/v1/expenses/")
        assert resp.status_code == 200

    def test_certifier_can_list_expenses(self, db, api_for, certifier):
        client = api_for(certifier)
        resp = client.get("/api/v1/expenses/")
        assert resp.status_code == 200


class TestExpenseReceiptsHTTP:
    def _make_png(self, name="receipt.png"):
        """A tiny valid PNG (1x1 pixel)."""
        import base64

        # A 1x1 transparent PNG, base64-encoded.
        png_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
            "YAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        )
        return SimpleUploadedFile(
            name,
            base64.b64decode(png_b64),
            content_type="image/png",
        )

    def test_record_expense_with_receipt(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.post(
            "/api/v1/expenses/",
            {
                "description": "AGM venue with receipt",
                "amount": "500.00",
                "expense_account_code": "5101",
                "payment_date": "2026-06-30",
                "receipt": self._make_png(),
            },
            format="multipart",
        )
        assert resp.status_code == 201, resp.content
        assert resp.data["receipt"] is not None
        assert resp.data["receipt_url"] is not None

    def test_record_expense_without_receipt(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.post(
            "/api/v1/expenses/",
            {
                "description": "No receipt",
                "amount": "100.00",
                "expense_account_code": "5101",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["receipt"] is None
        assert resp.data["receipt_url"] is None

    def test_reject_oversized_receipt(self, db, api_for, maker):
        client = api_for(maker)
        big = SimpleUploadedFile(
            "big.pdf",
            b"x" * (5 * 1024 * 1024 + 1),
            content_type="application/pdf",
        )
        resp = client.post(
            "/api/v1/expenses/",
            {
                "description": "Too big",
                "amount": "100.00",
                "expense_account_code": "5101",
                "receipt": big,
            },
            format="multipart",
        )
        assert resp.status_code == 400

    def test_reject_unsupported_extension(self, db, api_for, maker):
        client = api_for(maker)
        bad = SimpleUploadedFile(
            "virus.exe",
            b"malicious",
            content_type="application/octet-stream",
        )
        resp = client.post(
            "/api/v1/expenses/",
            {
                "description": "Bad file",
                "amount": "100.00",
                "expense_account_code": "5101",
                "receipt": bad,
            },
            format="multipart",
        )
        assert resp.status_code == 400

    def test_pipeline_summary_reports_receipt(self, db, api_for, maker, checker):
        maker_c = api_for(maker)
        maker_c.post(
            "/api/v1/expenses/",
            {
                "description": "Sum test",
                "amount": "250.00",
                "expense_account_code": "5101",
                "receipt": self._make_png(),
            },
            format="multipart",
        )

        checker_c = api_for(checker)
        resp = checker_c.get("/api/v1/pipeline/pending-check/")
        rows = [x for x in resp.data if x["transaction_type"] == "EXPENSE"]
        assert len(rows) >= 1
        summary = rows[-1]["target_summary"]
        assert summary["has_receipt"] is True
        assert summary["receipt_url"] is not None


# ====================================================================
# SHU
# ====================================================================
class TestShuHTTP:
    def _seed_fy(self, maria):
        fy = ShuFiscalYearFactory()
        ShuWeightingBaseFactory(
            fy=fy,
            member=maria,
            sum_weighted_balance=Decimal("780000.00"),
            months_active=12,
            weighted_savings_units=Decimal("65000.00"),
            loan_interest_paid=Decimal("600.00"),
        )
        return fy

    def test_calculate_shu(self, db, api_for, maker, maria):
        fy = self._seed_fy(maria)
        client = api_for(maker)
        resp = client.post(
            "/api/v1/shu/calculate/",
            {"fy_id": str(fy.id)},
            format="json",
        )
        assert resp.status_code == 201, resp.content
        assert resp.data["status"] == "PENDING_CHECK"
        # conftest seeds an equal 25/25/25/25 shu_split.
        assert resp.data["reserva_legal_amt"] == "32615.30"
        assert resp.data["admin_fund_amt"] == "32615.30"
        assert resp.data["jasa_simpanan_amt"] == "32615.30"
        assert resp.data["jasa_bunga_amt"] == "32615.30"

    def test_shu_detail(self, db, api_for, maker, board, maria):
        fy = self._seed_fy(maria)
        maker_c = api_for(maker)
        r = maker_c.post("/api/v1/shu/calculate/", {"fy_id": str(fy.id)}, format="json")
        calc_id = r.data["id"]

        board_c = api_for(board)
        resp = board_c.get(f"/api/v1/shu/{calc_id}/")
        assert resp.status_code == 200
        assert resp.data["id"] == calc_id

    def test_shu_full_payout_flow(self, db, api_for, maker, checker, certifier, maria):
        fy = self._seed_fy(maria)
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        r = maker_c.post("/api/v1/shu/calculate/", {"fy_id": str(fy.id)}, format="json")
        assert r.status_code == 201, r.content
        calc_id = r.data["id"]

        calc = ShuCalculation.objects.get(id=calc_id)
        actor_id = str(calc.pipeline_actor_id)

        _run_pipeline(checker_c, certifier_c, actor_id)

        calc.refresh_from_db()
        assert calc.status == "PAYOUT_COMPLETE"

        fy.refresh_from_db()
        assert fy.status == "CLOSED"

    def test_shu_payouts_list(self, db, api_for, maker, board, maria):
        fy = self._seed_fy(maria)
        maker_c = api_for(maker)
        r = maker_c.post("/api/v1/shu/calculate/", {"fy_id": str(fy.id)}, format="json")
        calc_id = r.data["id"]

        # Compute payouts via check step
        from shu.services.calculation import compute_member_payouts

        calc = ShuCalculation.objects.get(id=calc_id)
        compute_member_payouts(calc)

        board_c = api_for(board)
        resp = board_c.get(f"/api/v1/shu/{calc_id}/payouts/")
        assert resp.status_code == 200
        assert len(resp.data) >= 1
        assert "net_payout" in resp.data[0]

    def test_list_fiscal_years(self, db, api_for, checker):
        ShuFiscalYearFactory()
        client = api_for(checker)
        resp = client.get("/api/v1/shu/fiscal-years/")
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_superadmin_creates_fiscal_year(self, db, api_for, superadmin):
        client = api_for(superadmin)
        resp = client.post(
            "/api/v1/shu/fiscal-years/",
            {"year_start": "2025-07-01", "year_end": "2026-06-30"},
            format="json",
        )
        assert resp.status_code == 201, resp.content
        assert resp.data["status"] == "OPEN"

    def test_maker_cannot_create_fiscal_year(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.post(
            "/api/v1/shu/fiscal-years/",
            {"year_start": "2025-07-01", "year_end": "2026-06-30"},
            format="json",
        )
        assert resp.status_code == 403

    def test_superadmin_backfills_snapshots(self, db, api_for, superadmin, maria):
        fy = ShuFiscalYearFactory()
        client = api_for(superadmin)
        resp = client.post(
            "/api/v1/shu/backfill/",
            {"fy_id": str(fy.id)},
            format="json",
        )
        assert resp.status_code == 200
        assert "rows_created" in resp.data

    def test_maker_can_list_fiscal_years(self, db, api_for, maker):
        ShuFiscalYearFactory()
        client = api_for(maker)
        resp = client.get("/api/v1/shu/fiscal-years/")
        assert resp.status_code == 200

    def test_certifier_can_list_fiscal_years(self, db, api_for, certifier):
        ShuFiscalYearFactory()
        client = api_for(certifier)
        resp = client.get("/api/v1/shu/fiscal-years/")
        assert resp.status_code == 200

    def test_maker_can_view_fiscal_year_detail(self, db, api_for, maker):
        fy = ShuFiscalYearFactory()
        client = api_for(maker)
        resp = client.get(f"/api/v1/shu/fiscal-years/{fy.id}/")
        assert resp.status_code == 200

    def test_superadmin_can_calculate_shu(self, db, api_for, superadmin, maria):
        fy = self._seed_fy(maria)
        client = api_for(superadmin)
        resp = client.post(
            "/api/v1/shu/calculate/",
            {"fy_id": str(fy.id)},
            format="json",
        )
        assert resp.status_code == 201, resp.content
        assert resp.data["status"] == "PENDING_CHECK"

    def test_maker_can_view_own_calculation(self, db, api_for, maker, maria):
        fy = self._seed_fy(maria)
        client = api_for(maker)
        r = client.post(
            "/api/v1/shu/calculate/",
            {"fy_id": str(fy.id)},
            format="json",
        )
        calc_id = r.data["id"]

        # Maker can now view the calculation they just created
        resp = client.get(f"/api/v1/shu/{calc_id}/")
        assert resp.status_code == 200
        assert resp.data["id"] == calc_id

    def test_maker_can_view_payouts(self, db, api_for, maker, maria):
        from shu.services.calculation import compute_member_payouts

        fy = self._seed_fy(maria)
        client = api_for(maker)
        r = client.post(
            "/api/v1/shu/calculate/",
            {"fy_id": str(fy.id)},
            format="json",
        )
        calc = ShuCalculation.objects.get(id=r.data["id"])
        compute_member_payouts(calc)

        resp = client.get(f"/api/v1/shu/{calc.id}/payouts/")
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_fetch_calculation_by_fy(self, db, api_for, maker, maria):
        fy = self._seed_fy(maria)
        client = api_for(maker)

        # No calculation yet
        r0 = client.get(f"/api/v1/shu/fiscal-years/{fy.id}/calculation/")
        assert r0.status_code == 204

        # Create one
        r1 = client.post(
            "/api/v1/shu/calculate/",
            {"fy_id": str(fy.id)},
            format="json",
        )
        assert r1.status_code == 201

        # Now fetch it
        r2 = client.get(f"/api/v1/shu/fiscal-years/{fy.id}/calculation/")
        assert r2.status_code == 200
        assert r2.data["id"] == r1.data["id"]


# ====================================================================
# Governance
# ====================================================================
class TestGovernanceHTTP:
    def test_list_active_config(self, db, api_for, board):
        client = api_for(board)
        resp = client.get("/api/v1/governance/config/")
        assert resp.status_code == 200
        keys = {row["parameter_key"] for row in resp.data}
        assert "shu_split" in keys

    def test_propose_change(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.post(
            "/api/v1/governance/config/propose/",
            {
                "parameter_key": "obligatory_savings_monthly_cap",
                "proposed_value": 25,
                "effective_from": "2027-01-01",
            },
            format="json",
        )
        assert resp.status_code == 201, resp.content
        assert resp.data["status"] == "PENDING_CHECK"

    def test_propose_unknown_parameter(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.post(
            "/api/v1/governance/config/propose/",
            {
                "parameter_key": "not_a_real_key",
                "proposed_value": {"x": 1},
                "effective_from": "2027-01-01",
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_certify_change(self, db, api_for, maker, certifier):
        maker_c = api_for(maker)
        certifier_c = api_for(certifier)

        r = maker_c.post(
            "/api/v1/governance/config/propose/",
            {
                "parameter_key": "obligatory_savings_monthly_cap",
                "proposed_value": 30,
                "effective_from": "2027-01-01",
            },
            format="json",
        )
        change_id = r.data["id"]

        # Manually bump to PENDING_CERTIFY (bypassing pipeline for simplicity)
        change = GlobalConfigChange.objects.get(id=change_id)
        change.status = GlobalConfigChange.Status.PENDING_CERTIFY
        change.save(update_fields=["status"])

        resp = certifier_c.post(
            f"/api/v1/governance/config/certify/{change_id}/",
            format="json",
        )
        assert resp.status_code == 200, resp.content
        assert resp.data["status"] == "CERTIFIED"

        # Confirm it landed in global_config
        active = GlobalConfig.objects.filter(
            parameter_key="obligatory_savings_monthly_cap",
            status="ACTIVE",
            effective_from="2027-01-01",
        ).first()
        assert active is not None
        assert active.parameter_value == 30

    def test_list_changes(self, db, api_for, maker, board):
        maker_c = api_for(maker)
        maker_c.post(
            "/api/v1/governance/config/propose/",
            {
                "parameter_key": "loan_interest_rate_range",
                "proposed_value": {"min": 0.01, "max": 0.025},
                "effective_from": "2027-01-01",
            },
            format="json",
        )

        board_c = api_for(board)
        resp = board_c.get("/api/v1/governance/changes/")
        assert resp.status_code == 200
        assert len(resp.data) >= 1


class TestGovernanceValidationHTTP:
    def _post(self, client, payload):
        return client.post(
            "/api/v1/governance/config/propose/",
            payload,
            format="json",
        )

    def test_missing_keys_rejected_with_400(self, db, api_for, maker):
        """Regression: previously this 500'd."""
        client = api_for(maker)
        resp = self._post(
            client,
            {
                "parameter_key": "shu_split",
                "proposed_value": {"reserva_legal_pct": 30},  # 3 keys missing
                "effective_from": "2027-01-01",
            },
        )
        assert resp.status_code == 400, resp.content
        # The error should point at the missing fields.
        assert "proposed_value" in resp.data

    def test_empty_proposed_value_rejected(self, db, api_for, maker):
        client = api_for(maker)
        resp = self._post(
            client,
            {
                "parameter_key": "shu_split",
                "proposed_value": {},
                "effective_from": "2027-01-01",
            },
        )
        assert resp.status_code == 400

    def test_non_object_proposed_value_rejected(self, db, api_for, maker):
        client = api_for(maker)
        resp = self._post(
            client,
            {
                "parameter_key": "shu_split",
                "proposed_value": "hello",
                "effective_from": "2027-01-01",
            },
        )
        assert resp.status_code == 400

    def test_art69_blocks_low_reserva_when_below_capital(
        self, db, api_for, maker, certifier
    ):
        """
        A valid-shaped split with reserva_legal_pct < 25% must be rejected
        by Art. 69 once there is capital on the books and no reserve.
        Should be a clean 400, never a 500.
        """
        from decimal import Decimal

        from ledger.services import post_journal_entry

        # Seed capital so reserva (0) < kapital (1000) is True.
        post_journal_entry(
            description="Seed capital for Art.69 test",
            lines=[
                ("1001", "DEBIT", Decimal("1000.00")),
                ("3101", "CREDIT", Decimal("1000.00")),
            ],
            created_by=maker,
            auto_certify=True,
            certified_by=certifier,
        )

        client = api_for(maker)
        resp = self._post(
            client,
            {
                "parameter_key": "shu_split",
                "proposed_value": {
                    "reserva_legal_pct": 10,  # < 25 → Art. 69 should fire
                    "admin_fund_pct": 40,
                    "jasa_simpanan_pct": 25,
                    "jasa_bunga_pct": 25,  # sum = 100 → shape is valid
                },
                "effective_from": "2027-01-01",
            },
        )
        assert resp.status_code == 400, resp.content
        # The error should reference the legal reserve rule.
        assert "reserva" in str(resp.data).lower() or "art" in str(resp.data).lower()

    def test_sum_not_100_rejected(self, db, api_for, maker):
        client = api_for(maker)
        resp = self._post(
            client,
            {
                "parameter_key": "shu_split",
                "proposed_value": {
                    "reserva_legal_pct": 30,
                    "admin_fund_pct": 30,
                    "jasa_simpanan_pct": 20,
                    "jasa_bunga_pct": 10,  # sums to 90
                },
                "effective_from": "2027-01-01",
            },
        )
        assert resp.status_code == 400

    def test_non_numeric_pct_rejected(self, db, api_for, maker):
        client = api_for(maker)
        resp = self._post(
            client,
            {
                "parameter_key": "shu_split",
                "proposed_value": {
                    "reserva_legal_pct": "abc",
                    "admin_fund_pct": 30,
                    "jasa_simpanan_pct": 25,
                    "jasa_bunga_pct": 35,
                },
                "effective_from": "2027-01-01",
            },
        )
        assert resp.status_code == 400

    def test_negative_pct_rejected(self, db, api_for, maker):
        client = api_for(maker)
        resp = self._post(
            client,
            {
                "parameter_key": "shu_split",
                "proposed_value": {
                    "reserva_legal_pct": -5,
                    "admin_fund_pct": 40,
                    "jasa_simpanan_pct": 30,
                    "jasa_bunga_pct": 35,
                },
                "effective_from": "2027-01-01",
            },
        )
        assert resp.status_code == 400

    def test_obligatory_cap_shape_enforced(self, db, api_for, maker):
        client = api_for(maker)
        resp = self._post(
            client,
            {
                "parameter_key": "obligatory_savings_monthly_cap",
                "proposed_value": {"amount": 25},  # must be a bare number, not an object
                "effective_from": "2027-01-01",
            },
        )
        assert resp.status_code == 400

    def test_loan_rate_min_greater_than_max_rejected(self, db, api_for, maker):
        client = api_for(maker)
        resp = self._post(
            client,
            {
                "parameter_key": "loan_interest_rate_range",
                "proposed_value": {"min": 0.03, "max": 0.01},
                "effective_from": "2027-01-01",
            },
        )
        assert resp.status_code == 400


# ====================================================================
# Reports
# ====================================================================
class TestReportsHTTP:
    def test_dashboard(self, db, api_for, checker):
        client = api_for(checker)
        resp = client.get("/api/v1/reports/dashboard/")
        assert resp.status_code == 200
        assert "members" in resp.data
        assert "savings" in resp.data
        assert "loans" in resp.data
        assert "pipeline" in resp.data
        assert "recent_activity" in resp.data

    def test_trial_balance(self, db, api_for, board):
        client = api_for(board)
        resp = client.get("/api/v1/reports/trial-balance/?as_of=2026-06-30")
        assert resp.status_code == 200
        assert isinstance(resp.data, list)

    def test_income_statement(self, db, api_for, board):
        client = api_for(board)
        resp = client.get(
            "/api/v1/reports/income-statement/?start=2025-07-01&end=2026-06-30"
        )
        assert resp.status_code == 200
        assert "net_surplus" in resp.data

    def test_balance_sheet(self, db, api_for, board):
        client = api_for(board)
        resp = client.get("/api/v1/reports/balance-sheet/?as_of=2026-06-30")
        assert resp.status_code == 200
        assert "balanced" in resp.data
        assert "total_assets" in resp.data

    def test_maker_cannot_access_reports(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.get("/api/v1/reports/trial-balance/?as_of=2026-06-30")
        assert resp.status_code == 403

    def test_trial_balance_pdf(self, db, api_for, board):
        client = api_for(board)
        resp = client.get("/api/v1/reports/trial-balance/pdf/?as_of=2026-06-30")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"
        # PDF files start with the magic bytes %PDF
        assert resp.content[:4] == b"%PDF"

    def test_income_statement_pdf(self, db, api_for, board):
        client = api_for(board)
        resp = client.get(
            "/api/v1/reports/income-statement/pdf/" "?start=2025-07-01&end=2026-06-30"
        )
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"

    def test_balance_sheet_pdf(self, db, api_for, board):
        client = api_for(board)
        resp = client.get("/api/v1/reports/balance-sheet/pdf/?as_of=2026-06-30")
        assert resp.status_code == 200
        assert resp.content[:4] == b"%PDF"

    def test_surplus_distribution_pdf(self, db, api_for, board):
        fy = ShuFiscalYearFactory()
        client = api_for(board)
        resp = client.get(f"/api/v1/reports/surplus-distribution/{fy.id}/pdf/")
        assert resp.status_code == 200
        assert resp.content[:4] == b"%PDF"

    def test_trial_balance_pdf_requires_as_of(self, db, api_for, board):
        client = api_for(board)
        resp = client.get("/api/v1/reports/trial-balance/pdf/")
        assert resp.status_code == 400

    def test_maker_cannot_download_pdf(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.get("/api/v1/reports/trial-balance/pdf/?as_of=2026-06-30")
        assert resp.status_code == 403


# ====================================================================
# Pipeline
# ====================================================================
class TestPipelineHTTP:
    def _make_pending_deposit(self, maker_c, maria):
        """Helper — creates a pending deposit and returns the actor id."""
        r = maker_c.post(
            "/api/v1/savings/deposit/",
            {"member": str(maria.id), "amount": "100.00"},
            format="json",
        )
        assert r.status_code == 201, r.content
        return r.data["pipeline_actor"]

    def test_pending_check_queue(self, db, api_for, maker, checker, maria):
        maker_c = api_for(maker)
        actor_id = self._make_pending_deposit(maker_c, maria)

        checker_c = api_for(checker)
        resp = checker_c.get("/api/v1/pipeline/pending-check/")
        assert resp.status_code == 200
        ids = [str(row["id"]) for row in resp.data]
        assert str(actor_id) in ids

    def test_check_moves_to_pending_certify(self, db, api_for, maker, checker, maria):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        actor_id = self._make_pending_deposit(maker_c, maria)

        resp = checker_c.post(f"/api/v1/pipeline/{actor_id}/check/", format="json")
        assert resp.status_code == 200
        assert resp.data["status"] == "PENDING_CERTIFY"
        assert resp.data["checker_username"] == checker.user.username

    def test_certify_completes(self, db, api_for, maker, checker, certifier, maria):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)
        actor_id = self._make_pending_deposit(maker_c, maria)

        checker_c.post(f"/api/v1/pipeline/{actor_id}/check/", format="json")
        resp = certifier_c.post(f"/api/v1/pipeline/{actor_id}/certify/", format="json")
        assert resp.status_code == 200
        assert resp.data["status"] == "COMPLETED"
        assert resp.data["certifier_username"] == certifier.user.username

    def test_reject_flow(self, db, api_for, maker, checker, maria):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        actor_id = self._make_pending_deposit(maker_c, maria)

        resp = checker_c.post(
            f"/api/v1/pipeline/{actor_id}/reject/",
            {"reason": "documentation missing"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["status"] == "REJECTED"

    def test_maker_cannot_check_own_transaction(self, db, api_for, maker, maria):
        maker_c = api_for(maker)
        actor_id = self._make_pending_deposit(maker_c, maria)

        # Maker tries to check their own transaction
        resp = maker_c.post(f"/api/v1/pipeline/{actor_id}/check/", format="json")
        # Maker doesn't have CHECKER role → 403
        assert resp.status_code == 403

    def test_pending_check_includes_target_summary(
    self, db, api_for, maker, checker, maria
):
        maker_c = api_for(maker)
        actor_id = self._make_pending_deposit(maker_c, maria)

        checker_c = api_for(checker)
        resp = checker_c.get("/api/v1/pipeline/pending-check/")
        assert resp.status_code == 200

        row = next(r for r in resp.data if str(r["id"]) == str(actor_id))
        summary = row["target_summary"]
        assert summary is not None
        assert summary["kind"] == "DEPOSIT"
        assert summary["member_number"] == maria.membership_number
        assert "Deposit" in summary["label"]
        assert summary["amount"] == "100.00"

    def test_member_onboard_summary(self, db, api_for, maker, checker):
        maker_c = api_for(maker)

        # Create a pending member
        r = maker_c.post("/api/v1/members/", {
            "first_name": "Sum", "last_name": "Mary",
            "phone_number": "77000888",
            "date_of_birth": "1990-01-01",
        }, format="json")
        member_id = r.data["id"]

        # Pay initial capital
        r2 = maker_c.post(
            f"/api/v1/members/{member_id}/initial-capital/",
            {"amount": "50.00"},
            format="json",
        )
        actor_id = r2.data["pipeline_actor_id"]

        checker_c = api_for(checker)
        resp = checker_c.get("/api/v1/pipeline/pending-check/")
        row = next(r for r in resp.data if str(r["id"]) == str(actor_id))
        summary = row["target_summary"]
        assert summary["kind"] == "INITIAL_CAPITAL"
        assert "Initial capital" in summary["label"]
        assert summary["amount"] == "50.00"


# ====================================================================
# Reversal UI
# ====================================================================
class TestReversalHTTP:
    def _make_certified_deposit(self, maker_c, checker_c, certifier_c, maria):
        """Helper — creates a completed deposit and returns its JE and Transaction IDs."""
        r = maker_c.post(
            "/api/v1/savings/deposit/",
            {"member": str(maria.id), "amount": "500.00"},
            format="json",
        )
        actor_id = r.data["pipeline_actor"]
        txn_id = r.data["id"]

        checker_c.post(f"/api/v1/pipeline/{actor_id}/check/", format="json")
        certifier_c.post(f"/api/v1/pipeline/{actor_id}/certify/", format="json")

        from savings.models import Transaction

        txn = Transaction.objects.get(id=txn_id)
        return str(txn.journal_entry_id), txn_id

    def test_create_reversal(self, db, api_for, maker, checker, certifier, maria):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        je_id, txn_id = self._make_certified_deposit(
            maker_c, checker_c, certifier_c, maria
        )

        resp = maker_c.post(
            "/api/v1/ledger/reversals/",
            {
                "original_journal_entry": je_id,
                "source_type": "SAVINGS_TRANSACTION",
                "source_id": str(txn_id),
                "reason": "Member reports wrong amount",
            },
            format="json",
        )
        assert resp.status_code == 201, resp.content
        assert resp.data["status"] == "PENDING_CHECK"

    def test_cannot_reverse_draft_entry(self, db, api_for, maker, maria):
        from decimal import Decimal

        from ledger.services import post_journal_entry

        je = post_journal_entry(
            description="draft",
            lines=[
                ("1001", "DEBIT", Decimal("10.00")),
                ("3101", "CREDIT", Decimal("10.00")),
            ],
            created_by=maker,
        )

        client = api_for(maker)
        resp = client.post(
            "/api/v1/ledger/reversals/",
            {
                "original_journal_entry": str(je.id),
                "source_type": "OTHER",
                "reason": "test",
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_double_reversal_blocked(
        self, db, api_for, maker, checker, certifier, maria
    ):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        je_id, txn_id = self._make_certified_deposit(
            maker_c, checker_c, certifier_c, maria
        )

        # First reversal
        r1 = maker_c.post(
            "/api/v1/ledger/reversals/",
            {
                "original_journal_entry": je_id,
                "source_type": "SAVINGS_TRANSACTION",
                "source_id": str(txn_id),
                "reason": "First reversal",
            },
            format="json",
        )
        assert r1.status_code == 201
        checker_c.post(
            f"/api/v1/pipeline/{r1.data['pipeline_actor']}/check/", format="json"
        )
        certifier_c.post(
            f"/api/v1/pipeline/{r1.data['pipeline_actor']}/certify/", format="json"
        )

        # Second attempt should be blocked
        r2 = maker_c.post(
            "/api/v1/ledger/reversals/",
            {
                "original_journal_entry": je_id,
                "source_type": "SAVINGS_TRANSACTION",
                "source_id": str(txn_id),
                "reason": "Second attempt",
            },
            format="json",
        )
        assert r2.status_code == 400

    def test_full_reversal_flow_updates_balances(
        self, db, api_for, maker, checker, certifier, maria
    ):
        maker_c = api_for(maker)
        checker_c = api_for(checker)
        certifier_c = api_for(certifier)

        # Deposit 500 → capital goes up 20, voluntary up 480
        je_id, txn_id = self._make_certified_deposit(
            maker_c, checker_c, certifier_c, maria
        )

        maria.refresh_from_db()
        capital_after_deposit = maria.kapital_sosial_balance
        voluntary_after_deposit = maria.voluntary_deposit.balance_available

        # Reverse it
        r = maker_c.post(
            "/api/v1/ledger/reversals/",
            {
                "original_journal_entry": je_id,
                "source_type": "SAVINGS_TRANSACTION",
                "source_id": str(txn_id),
                "reason": "Wrong amount recorded",
            },
            format="json",
        )
        actor_id = r.data["pipeline_actor"]

        checker_c.post(f"/api/v1/pipeline/{actor_id}/check/", format="json")
        certifier_c.post(f"/api/v1/pipeline/{actor_id}/certify/", format="json")

        maria.refresh_from_db()
        # Balances should be back to pre-deposit values
        assert maria.kapital_sosial_balance == capital_after_deposit - Decimal("20.00")
        assert (
            maria.voluntary_deposit.balance_available
            == voluntary_after_deposit - Decimal("480.00")
        )

        # The source transaction should now be REVERSED
        from savings.models import Transaction

        txn = Transaction.objects.get(id=txn_id)
        assert txn.status == "REVERSED"

    def test_list_reversals(self, db, api_for, maker, board):
        maker_c = api_for(maker)
        board_c = api_for(board)

        resp = board_c.get("/api/v1/ledger/reversals/")
        assert resp.status_code == 200
        assert isinstance(resp.data, list)

    def test_maker_cannot_read_reversals_of_others(self, db, api_for, maker):
        """Maker can read the list (they need to track their own)."""
        client = api_for(maker)
        resp = client.get("/api/v1/ledger/reversals/")
        assert resp.status_code == 200


# ====================================================================
# AUDIT
# ====================================================================
class TestAuditHTTP:
    def _seed_audit(self, actor):
        from audit.models import AuditLog

        AuditLog.objects.create(
            actor=actor,
            action="LOGIN_SUCCESS",
            target_type="USER",
            target_repr=actor.user.username,
            description="Test login",
        )
        AuditLog.objects.create(
            actor=actor,
            action="USER_CREATED",
            target_type="USER",
            target_repr="newuser",
            description="Test user creation",
        )

    def test_superadmin_can_list_audit(self, db, api_for, superadmin):
        self._seed_audit(superadmin)
        client = api_for(superadmin)
        resp = client.get("/api/v1/audit/log/")
        assert resp.status_code == 200
        assert resp.data["count"] >= 2

    def test_board_can_list_audit(self, db, api_for, superadmin, board):
        self._seed_audit(superadmin)
        client = api_for(board)
        resp = client.get("/api/v1/audit/log/")
        assert resp.status_code == 200

    def test_maker_cannot_list_audit(self, db, api_for, maker):
        client = api_for(maker)
        resp = client.get("/api/v1/audit/log/")
        assert resp.status_code == 403

    def test_filter_by_action(self, db, api_for, superadmin):
        self._seed_audit(superadmin)
        client = api_for(superadmin)
        resp = client.get("/api/v1/audit/log/?action=LOGIN_SUCCESS")
        assert resp.status_code == 200
        for row in resp.data["results"]:
            assert row["action"] == "LOGIN_SUCCESS"

    def test_export_csv(self, db, api_for, superadmin):
        self._seed_audit(superadmin)
        client = api_for(superadmin)
        resp = client.get("/api/v1/audit/log/export/")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"
        assert b"Timestamp" in resp.content
        assert b"LOGIN_SUCCESS" in resp.content

    def test_ledger_activity_list(self, db, api_for, superadmin):
        client = api_for(superadmin)
        resp = client.get("/api/v1/audit/ledger/")
        assert resp.status_code == 200
        assert "results" in resp.data

    def test_login_success_is_logged(self, db, maker):
        """Obtaining a JWT records a LOGIN_SUCCESS audit entry."""
        from audit.models import AuditLog

        client = APIClient()
        resp = client.post(
            "/api/v1/auth/token/",
            {"username": maker.user.username, "password": "testpass123"},
            format="json",
        )
        assert resp.status_code == 200
        assert AuditLog.objects.filter(
            action="LOGIN_SUCCESS",
            actor=maker,
        ).exists()

    def test_login_failure_is_logged(self, db, maker):
        from audit.models import AuditLog

        client = APIClient()
        client.post(
            "/api/v1/auth/token/",
            {"username": maker.user.username, "password": "wrongpass"},
            format="json",
        )
        assert AuditLog.objects.filter(action="LOGIN_FAILURE").exists()


# ====================================================================
# NOTIFICATIONS
# ====================================================================
class TestNotificationsHTTP:
    def test_checker_sees_pending_check_items(self, db, api_for, maker, checker, maria):
        maker_c = api_for(maker)
        maker_c.post(
            "/api/v1/savings/deposit/",
            {"member": str(maria.id), "amount": "100.00"},
            format="json",
        )

        checker_c = api_for(checker)
        resp = checker_c.get("/api/v1/audit/notifications/")
        assert resp.status_code == 200
        assert resp.data["count"] >= 1
        queues = {i["queue"] for i in resp.data["items"]}
        assert "PENDING_CHECK" in queues

    def test_certifier_sees_pending_certify_items(
        self, db, api_for, maker, checker, certifier, maria
    ):
        maker_c = api_for(maker)
        r = maker_c.post(
            "/api/v1/savings/deposit/",
            {"member": str(maria.id), "amount": "100.00"},
            format="json",
        )
        actor_id = r.data["pipeline_actor"]
        checker_c = api_for(checker)
        checker_c.post(f"/api/v1/pipeline/{actor_id}/check/", format="json")

        certifier_c = api_for(certifier)
        resp = certifier_c.get("/api/v1/audit/notifications/")
        assert resp.status_code == 200
        queues = {i["queue"] for i in resp.data["items"]}
        assert "PENDING_CERTIFY" in queues

    def test_maker_sees_rejected_items(self, db, api_for, maker, checker, maria):
        maker_c = api_for(maker)
        r = maker_c.post(
            "/api/v1/savings/deposit/",
            {"member": str(maria.id), "amount": "100.00"},
            format="json",
        )
        actor_id = r.data["pipeline_actor"]

        checker_c = api_for(checker)
        checker_c.post(
            f"/api/v1/pipeline/{actor_id}/reject/",
            {"reason": "test rejection"},
            format="json",
        )

        resp = maker_c.get("/api/v1/audit/notifications/")
        assert resp.status_code == 200
        queues = {i["queue"] for i in resp.data["items"]}
        assert "REJECTED" in queues

    def test_board_sees_empty_notifications(self, db, api_for, board):
        client = api_for(board)
        resp = client.get("/api/v1/audit/notifications/")
        assert resp.status_code == 200
        assert resp.data["count"] == 0

    def test_unauthenticated_returns_401(self, db):
        client = APIClient()
        resp = client.get("/api/v1/audit/notifications/")
        assert resp.status_code == 401


class TestNotFound404:
    """Regression: plain .get(pk=...) used to 500 on missing IDs."""

    BAD_UUID = "00000000-0000-0000-0000-000000000000"

    def test_pipeline_actor_missing_returns_404(self, db, api_for, checker):
        client = api_for(checker)
        resp = client.post(f"/api/v1/pipeline/{self.BAD_UUID}/check/", format="json")
        assert resp.status_code == 404

    def test_expense_missing_returns_404(self, db, api_for, board):
        client = api_for(board)
        resp = client.get(f"/api/v1/expenses/{self.BAD_UUID}/")
        assert resp.status_code == 404

    def test_shu_fiscal_year_missing_returns_404(self, db, api_for, board):
        client = api_for(board)
        resp = client.get(f"/api/v1/shu/fiscal-years/{self.BAD_UUID}/")
        assert resp.status_code == 404

    def test_shu_calculation_missing_returns_404(self, db, api_for, board):
        client = api_for(board)
        resp = client.get(f"/api/v1/shu/{self.BAD_UUID}/")
        assert resp.status_code == 404

    def test_governance_change_missing_returns_404(self, db, api_for, certifier):
        client = api_for(certifier)
        resp = client.post(
            f"/api/v1/governance/config/certify/{self.BAD_UUID}/",
            format="json",
        )
        assert resp.status_code == 404

    def test_member_missing_returns_404(self, db, api_for, checker):
        client = api_for(checker)
        resp = client.get(f"/api/v1/members/{self.BAD_UUID}/")
        assert resp.status_code == 404


class TestReportDateValidation:
    def test_trial_balance_invalid_date_400(self, db, api_for, board):
        client = api_for(board)
        resp = client.get("/api/v1/reports/trial-balance/?as_of=2026-13-40")
        assert resp.status_code == 400
        assert "as_of" in resp.data

    def test_trial_balance_missing_date_400(self, db, api_for, board):
        client = api_for(board)
        resp = client.get("/api/v1/reports/trial-balance/")
        assert resp.status_code == 400

    def test_trial_balance_garbage_400(self, db, api_for, board):
        client = api_for(board)
        resp = client.get("/api/v1/reports/trial-balance/?as_of=abc")
        assert resp.status_code == 400

    def test_income_statement_invalid_end_400(self, db, api_for, board):
        client = api_for(board)
        resp = client.get(
            "/api/v1/reports/income-statement/?start=2026-01-01&end=not-a-date"
        )
        assert resp.status_code == 400

    def test_balance_sheet_pdf_invalid_date_400(self, db, api_for, board):
        client = api_for(board)
        resp = client.get("/api/v1/reports/balance-sheet/pdf/?as_of=nope")
        assert resp.status_code == 400

    def test_valid_date_still_works(self, db, api_for, board):
        client = api_for(board)
        resp = client.get("/api/v1/reports/trial-balance/?as_of=2026-06-30")
        assert resp.status_code == 200
