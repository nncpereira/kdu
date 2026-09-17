from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounting.models import Account
from core.exceptions import DomainError
from ledger.models import JournalEntry
from ledger.services import (
    post_journal_entry,
    certify_journal_entry,
    reverse_journal_entry,
    account_net_balance,
    UnbalancedEntryError,
    AccountNotFoundError,
)
from users.models import UserProfile

User = get_user_model()


class LedgerServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserProfile.objects.create(
            user=User.objects.create_user("maker", password="x"),
            role=UserProfile.Role.MAKER,
        )
        Account.objects.get_or_create(
            account_code="1001",
            defaults={"account_name": "Cash", "account_type": "ASSET"},
        )
        Account.objects.get_or_create(
            account_code="3101",
            defaults={"account_name": "Kapital", "account_type": "EQUITY"},
        )
        Account.objects.get_or_create(
            account_code="2101",
            defaults={"account_name": "Vol Dep", "account_type": "LIABILITY"},
        )
        Account.objects.get_or_create(
            account_code="40100",
            defaults={"account_name": "Interest", "account_type": "REVENUE"},
        )

    def test_post_balanced_entry(self):
        entry = post_journal_entry(
            description="Deposit 100",
            lines=[
                ("1001", "DEBIT", Decimal("100.00")),
                ("3101", "CREDIT", Decimal("100.00")),
            ],
            created_by=self.user,
        )
        self.assertEqual(entry.status, JournalEntry.Status.DRAFT)
        self.assertTrue(entry.is_balanced)

    def test_unbalanced_entry_rejected(self):
        with self.assertRaises(UnbalancedEntryError):
            post_journal_entry(
                description="Bad",
                lines=[
                    ("1001", "DEBIT", Decimal("100.00")),
                    ("3101", "CREDIT", Decimal("90.00")),
                ],
                created_by=self.user,
            )

    def test_missing_account_rejected(self):
        with self.assertRaises(AccountNotFoundError):
            post_journal_entry(
                description="Missing",
                lines=[
                    ("9999", "DEBIT", Decimal("100.00")),
                    ("3101", "CREDIT", Decimal("100.00")),
                ],
                created_by=self.user,
            )

    def test_account_net_balance(self):
        post_journal_entry(
            description="Deposit 200",
            lines=[
                ("1001", "DEBIT", Decimal("200.00")),
                ("3101", "CREDIT", Decimal("200.00")),
            ],
            created_by=self.user,
            auto_certify=True,
            certified_by=self.user,
        )
        self.assertEqual(account_net_balance("1001"), Decimal("200.00"))
        self.assertEqual(account_net_balance("3101"), Decimal("200.00"))

    def test_reversal(self):
        original = post_journal_entry(
            description="Expense entry",
            lines=[
                ("1001", "CREDIT", Decimal("50.00")),
                ("40100", "DEBIT", Decimal("50.00")),
            ],
            created_by=self.user,
            auto_certify=True,
            certified_by=self.user,
        )
        reversal = reverse_journal_entry(
            original,
            created_by=self.user,
            reason="Wrong",
            auto_certify=True,
            certified_by=self.user,
        )
        self.assertEqual(reversal.original_journal_entry_id, original.id)
        # Net effect on both accounts is now zero.
        self.assertEqual(account_net_balance("1001"), Decimal("0.00"))
        self.assertEqual(account_net_balance("40100"), Decimal("0.00"))

    def test_double_reversal_blocked(self):
        original = post_journal_entry(
            description="X",
            lines=[
                ("1001", "DEBIT", Decimal("10.00")),
                ("3101", "CREDIT", Decimal("10.00")),
            ],
            created_by=self.user,
            auto_certify=True,
            certified_by=self.user,
        )
        reverse_journal_entry(
            original, created_by=self.user, auto_certify=True, certified_by=self.user
        )
        with self.assertRaises(DomainError):
            reverse_journal_entry(
                original,
                created_by=self.user,
                auto_certify=True,
                certified_by=self.user,
            )

    def test_cannot_reverse_draft(self):
        draft = post_journal_entry(
            description="Draft",
            lines=[
                ("1001", "DEBIT", Decimal("5.00")),
                ("3101", "CREDIT", Decimal("5.00")),
            ],
            created_by=self.user,
        )
        with self.assertRaises(DomainError):
            reverse_journal_entry(draft, created_by=self.user)
