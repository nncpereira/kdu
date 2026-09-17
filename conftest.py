"""
Project-wide fixtures for the KDU test suite.
"""

import os
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection

from accounting.models import Account
from governance.models import GlobalConfig
from members.models import Member, MemberSequence
from users.models import UserProfile

User = get_user_model()


# ====================================================================
# Postgres availability guard
# ====================================================================
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "postgres_only: requires a working Postgres connection"
    )


@pytest.fixture(scope="session", autouse=True)
def _check_postgres(django_db_setup, django_db_blocker):
    """Fail early if Postgres is not reachable."""
    try:
        with django_db_blocker.unblock():
            with connection.cursor() as cur:
                cur.execute("SELECT version();")
                cur.fetchone()
    except Exception as e:
        pytest.exit(f"Postgres not reachable: {e}", returncode=1)


# ====================================================================
# Reference data — load once per test session
# ====================================================================
@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Seed the CoA and governance defaults once."""
    with django_db_blocker.unblock():
        _seed_coa()
        _seed_governance()


def _seed_coa():
    SEED = [
        ("1001", "Cash on Hand", "ASSET"),
        ("1301", "Loans Receivable", "ASSET"),
        ("2101", "Member Voluntary Deposits", "LIABILITY"),
        ("3101", "Kapital Sosial", "EQUITY"),
        ("3200", "SHU Payable", "LIABILITY"),
        ("3501", "Reserva Legal", "EQUITY"),
        ("3502", "Admin & Operational Fund", "EQUITY"),
        ("3900", "Retained Surplus", "EQUITY"),
        ("40100", "Interest Income from Loans", "REVENUE"),
        ("5101", "AGM Expense", "EXPENSE"),
        ("5102", "Salaries Expense", "EXPENSE"),
        ("5103", "Utilities Expense", "EXPENSE"),
        ("5104", "Office Supplies Expense", "EXPENSE"),
    ]
    for code, name, atype in SEED:
        Account.objects.update_or_create(
            account_code=code,
            defaults={"account_name": name, "account_type": atype, "status": "ACTIVE"},
        )


def _seed_governance():
    if UserProfile.objects.filter(role=UserProfile.Role.SUPERADMIN).exists():
        admin = UserProfile.objects.filter(role=UserProfile.Role.SUPERADMIN).first()
    else:
        user = User.objects.create_user("sysadmin", password="x")
        admin = UserProfile.objects.create(user=user, role=UserProfile.Role.SUPERADMIN)

    GlobalConfig.objects.update_or_create(
        parameter_key="shu_split",
        effective_from="2025-01-01",
        defaults={
            "parameter_value": {
                "reserva_legal_pct": 10,
                "admin_fund_pct": 30,
                "jasa_simpanan_pct": 25,
                "jasa_bunga_pct": 35,
            },
            "status": "ACTIVE",
            "created_by": admin,
        },
    )
    GlobalConfig.objects.update_or_create(
        parameter_key="obligatory_savings_monthly_cap",
        effective_from="2025-01-01",
        defaults={
            "parameter_value": 20,
            "status": "ACTIVE",
            "created_by": admin,
        },
    )
    GlobalConfig.objects.update_or_create(
        parameter_key="loan_interest_rate_range",
        effective_from="2025-01-01",
        defaults={
            "parameter_value": {"min": 0.01, "max": 0.02},
            "status": "ACTIVE",
            "created_by": admin,
        },
    )


# ====================================================================
# Per-test isolation
# ====================================================================
@pytest.fixture(autouse=True)
def _reset_sequences(db):
    """Reset MemberSequence between tests to keep numbering predictable."""
    MemberSequence.objects.update_or_create(id=1, defaults={"last_value": 0})


# ====================================================================
# Staff users
# ====================================================================
@pytest.fixture
def maker(db):
    return _make_user("maker", UserProfile.Role.MAKER)


@pytest.fixture
def checker(db):
    return _make_user("checker", UserProfile.Role.CHECKER)


@pytest.fixture
def certifier(db):
    return _make_user("certifier", UserProfile.Role.CERTIFIER)


@pytest.fixture
def superadmin(db):
    return _make_user("admin", UserProfile.Role.SUPERADMIN)


@pytest.fixture
def board(db):
    return _make_user("board", UserProfile.Role.BOARD)


@pytest.fixture
def auditor(db):
    return _make_user("auditor", UserProfile.Role.AUDITOR)


def _make_user(username, role):
    user = User.objects.create_user(username=username, password="testpass123")
    return UserProfile.objects.create(user=user, role=role)


# ====================================================================
# Members
# ====================================================================
@pytest.fixture
def member_factory(db):
    from tests.factories.members import MemberFactory

    return MemberFactory


@pytest.fixture
def maria(member_factory):
    return member_factory(
        first_name="Maria",
        last_name="Test",
        date_joined="2024-05-10",
        kapital_sosial_balance=Decimal("50.00"),
    )


@pytest.fixture
def ana(member_factory):
    return member_factory(
        first_name="Ana",
        last_name="Test",
        date_joined="2025-08-02",
        kapital_sosial_balance=Decimal("50.00"),
    )


@pytest.fixture
def pedro(member_factory):
    return member_factory(
        first_name="Pedro",
        last_name="Test",
        date_joined="2025-12-15",
        kapital_sosial_balance=Decimal("50.00"),
    )


# ====================================================================
# Time travel
# ====================================================================
@pytest.fixture
def frozen_july_2025():
    from freezegun import freeze_time

    with freeze_time("2025-07-01 09:00:00"):
        yield


@pytest.fixture
def frozen_june_2026():
    from freezegun import freeze_time

    with freeze_time("2026-06-30 23:59:00"):
        yield
