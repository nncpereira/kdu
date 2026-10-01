"""
One-off import of KDU's real members from the parsed Member Booklet JSON
(produced by a scratch parsing script from "Member Booklet 2025-2026.xlsx").

This bypasses the maker-checker-certifier pipeline and posts directly to
the ledger with auto_certify=True, mirroring the trusted/system posting
path used by seed_shu_demo_data.py -- the goal here is to faithfully
replay each member's *exact* historical obligatory/voluntary split and
loan cash flows, not recompute them through today's deposit()/withdraw()
cap logic.

Known placeholders (source spreadsheets have no data for these):
  - phone_number: "00000000"
  - date_of_birth: 1900-01-01
  - date_joined: 2015-01-01 (treats every real member as pre-existing,
    i.e. eligible for the full FY2025-2026 SHU weighting)
  - Loan monthly_rate/term_months: 2%/mo, 12mo placeholder (SHU math only
    reads actual LoanRepayment.interest_paid, never these fields)

Usage:
    python manage.py import_real_members /path/to/members.json --confirm
"""

import json
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ledger.services import post_journal_entry
from loans.models import Loan, LoanRepayment
from members.models import Member, MemberOnboarding
from savings.models import Transaction as SavingsTxn
from users.models import UserProfile

CASH = "1001"
LOANS_RECEIVABLE = "1301"
KAPITAL_SOSIAL = "3101"
VOLUNTARY_DEPOSIT = "2101"
INTEREST_INCOME = "40100"

JOIN_DATE = date(2015, 1, 1)
PLACEHOLDER_PHONE = "00000000"
PLACEHOLDER_DOB = date(1900, 1, 1)


def D(x) -> Decimal:
    return Decimal(str(round(float(x), 2)))


def split_name(full_name: str):
    name = full_name.strip()
    if "/" in name:
        # Joint/household account -- keep the first-listed person only.
        name = name.split("/")[0].strip()
    parts = name.split()
    if len(parts) == 1:
        return parts[0], "", ""
    if len(parts) == 2:
        return parts[0], "", parts[1]
    return parts[0], " ".join(parts[1:-1]), parts[-1]


class Command(BaseCommand):
    help = "Import real KDU members from parsed Member Booklet JSON."

    def add_arguments(self, parser):
        parser.add_argument("json_path")
        parser.add_argument("--confirm", action="store_true")

    def handle(self, *args, **opts):
        if not opts["confirm"]:
            raise CommandError("Pass --confirm to run (this assumes the DB was already wiped/migrated).")

        with open(opts["json_path"]) as f:
            records = json.load(f)
        records.sort(key=lambda r: r["member_no"])

        try:
            maker = UserProfile.objects.get(user__username="maker1")
            certifier = UserProfile.objects.get(user__username="certifier1")
        except UserProfile.DoesNotExist:
            raise CommandError("maker1/certifier1 not found -- run `manage.py bootstrap` first.") from None

        joint_accounts = []
        neg_capital_events = []
        count = 0

        for rec in records:
            with transaction.atomic():
                member = self._import_member(rec, maker, certifier, neg_capital_events)
            if rec["is_joint"]:
                joint_accounts.append((member.membership_number, rec["name"]))
            count += 1
            if count % 25 == 0:
                self.stdout.write(f"  …{count}/{len(records)} members imported")

        self.stdout.write(self.style.SUCCESS(f"Imported {count} members."))
        if joint_accounts:
            self.stdout.write("\nJoint/household accounts (only the first-listed person was kept):")
            for no, name in joint_accounts:
                self.stdout.write(f"  {no}: {name}")
        if neg_capital_events:
            self.stdout.write("\nUnusual: obligatory-capital (SW) decreases replayed as-is (normally locked):")
            for line in neg_capital_events:
                self.stdout.write(f"  {line}")
        self.stdout.write(
            "\nAll imported members have placeholder phone_number='00000000', "
            "date_of_birth=1900-01-01, and date_joined=2015-01-01 -- "
            "flag for follow-up with real values."
        )

    # ----------------------------------------------------------------
    def _import_member(self, rec, maker, certifier, neg_capital_events):
        first, middle, last = split_name(rec["name"])
        member = Member.objects.create(
            salutation="Mr",
            first_name=first,
            middle_name=middle,
            last_name=last,
            phone_number=PLACEHOLDER_PHONE,
            date_of_birth=PLACEHOLDER_DOB,
            status=Member.Status.ACTIVE,
            date_joined=JOIN_DATE,
        )

        sp = D(rec["simpanan_pokok"])
        if sp > 0:
            je = post_journal_entry(
                description=f"Initial capital (imported) - {member.membership_number}",
                lines=[(CASH, "DEBIT", sp), (KAPITAL_SOSIAL, "CREDIT", sp, member)],
                created_by=maker,
                entry_date=JOIN_DATE,
                auto_certify=True,
                certified_by=certifier,
            )
            MemberOnboarding.objects.create(
                member=member,
                initial_capital_amount=sp,
                journal_entry=je,
                status=MemberOnboarding.Status.COMPLETED,
            )

        self._replay_savings(member, rec["savings_rows"], maker, certifier, neg_capital_events)
        self._replay_loans(member, rec["loan_rows"], maker, certifier)
        return member

    # ----------------------------------------------------------------
    def _replay_savings(self, member, rows, maker, certifier, neg_capital_events):
        prev_sw, prev_ss = Decimal("0"), Decimal("0")
        for row in rows:
            d = date.fromisoformat(row["date"])
            sw, ss = D(row["saldo_sw"]), D(row["saldo_ss"])
            d_sw, d_ss = sw - prev_sw, ss - prev_ss
            prev_sw, prev_ss = sw, ss
            if d_sw == 0 and d_ss == 0:
                continue

            dep_ob, dep_vol = max(d_sw, Decimal("0")), max(d_ss, Decimal("0"))
            wd_ob, wd_vol = max(-d_sw, Decimal("0")), max(-d_ss, Decimal("0"))

            if dep_ob > 0 or dep_vol > 0:
                amount = dep_ob + dep_vol
                lines = [(CASH, "DEBIT", amount)]
                if dep_ob > 0:
                    lines.append((KAPITAL_SOSIAL, "CREDIT", dep_ob, member))
                if dep_vol > 0:
                    lines.append((VOLUNTARY_DEPOSIT, "CREDIT", dep_vol, member))
                je = post_journal_entry(
                    description=f"Deposit (imported) - {member.membership_number}",
                    lines=lines, created_by=maker, entry_date=d,
                    auto_certify=True, certified_by=certifier,
                )
                SavingsTxn.objects.create(
                    member=member, transaction_type=SavingsTxn.Type.DEPOSIT,
                    requested_amount=amount, obligatory_portion=dep_ob,
                    voluntary_portion=dep_vol, status=SavingsTxn.Status.COMPLETED,
                    journal_entry=je,
                )

            if wd_ob > 0 or wd_vol > 0:
                amount = wd_ob + wd_vol
                lines = [(CASH, "CREDIT", amount)]
                if wd_vol > 0:
                    lines.append((VOLUNTARY_DEPOSIT, "DEBIT", wd_vol, member))
                if wd_ob > 0:
                    lines.append((KAPITAL_SOSIAL, "DEBIT", wd_ob, member))
                    neg_capital_events.append(f"{member.membership_number} on {d}: -{wd_ob}")
                je = post_journal_entry(
                    description=f"Withdrawal (imported) - {member.membership_number}",
                    lines=lines, created_by=maker, entry_date=d,
                    auto_certify=True, certified_by=certifier,
                )
                SavingsTxn.objects.create(
                    member=member, transaction_type=SavingsTxn.Type.WITHDRAWAL,
                    requested_amount=amount, obligatory_portion=wd_ob,
                    voluntary_portion=wd_vol, status=SavingsTxn.Status.COMPLETED,
                    journal_entry=je,
                )

    # ----------------------------------------------------------------
    def _replay_loans(self, member, rows, maker, certifier):
        # A "Total Loan" row is sometimes a brand-new loan cycle, sometimes
        # just a top-up drawn against the still-outstanding running balance
        # (the booklet tracks ONE continuous declining balance per member,
        # not independent parallel loans). Only start a new Loan record
        # once the previous one has actually been paid off.
        current_loan = None
        for row in rows:
            d = date.fromisoformat(row["date"])
            total_loan = D(row["total_loan"])
            if total_loan > 0:
                if current_loan is None or current_loan.principal_outstanding <= 0:
                    current_loan = Loan.objects.create(
                        member=member, principal_original=total_loan,
                        principal_outstanding=total_loan, monthly_rate=Decimal("0.02"),
                        term_months=12, status=Loan.Status.DISBURSED, disbursed_date=d,
                        purpose="Imported historical loan",
                    )
                else:
                    current_loan.principal_original += total_loan
                    current_loan.principal_outstanding += total_loan
                    current_loan.save(update_fields=["principal_original", "principal_outstanding", "updated_at"])
                post_journal_entry(
                    description=f"Loan disbursement (imported) - {member.membership_number}",
                    lines=[(LOANS_RECEIVABLE, "DEBIT", total_loan, member), (CASH, "CREDIT", total_loan)],
                    created_by=maker, entry_date=d, auto_certify=True, certified_by=certifier,
                )

            angsuran, bunga = D(row["angsuran"]), D(row["bunga"])
            if (angsuran > 0 or bunga > 0) and current_loan is not None:
                lines = [(CASH, "DEBIT", angsuran + bunga)]
                if bunga > 0:
                    lines.append((INTEREST_INCOME, "CREDIT", bunga, member))
                if angsuran > 0:
                    lines.append((LOANS_RECEIVABLE, "CREDIT", angsuran, member))
                je = post_journal_entry(
                    description=f"Loan repayment (imported) - {member.membership_number}",
                    lines=lines, created_by=maker, entry_date=d,
                    auto_certify=True, certified_by=certifier,
                )
                LoanRepayment.objects.create(
                    loan=current_loan, principal_paid=angsuran, interest_paid=bunga,
                    payment_date=d, mode="MANUAL", status=LoanRepayment.Status.COMPLETED,
                    journal_entry=je,
                )
                current_loan.principal_outstanding -= angsuran
                if current_loan.principal_outstanding <= 0:
                    current_loan.principal_outstanding = Decimal("0")
                    current_loan.status = Loan.Status.FULLY_REPAID
                current_loan.save(update_fields=["principal_outstanding", "status", "updated_at"])
