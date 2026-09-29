"""
Seed a realistic multi-year member/transaction dataset for testing the
accuracy of the SHU (dividend) split across members.

Requires `manage.py bootstrap` to have run first (needs the maker1/
checker1/certifier1 staff accounts it creates).

Usage:
    python manage.py seed_shu_demo_data
    python manage.py seed_shu_demo_data --count 150 --loan-pct 0.3
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from governance.models import GlobalConfig
from governance.services import propose_change
from loans.models import Loan
from loans.services import originate_loan, repay_scheduled
from members.models import Member
from members.services import pay_initial_capital
from pipeline.services import certify as pcertify
from pipeline.services import check as pcheck
from savings.services import deposit, withdraw
from shu.services.calculation import create_fiscal_year, run_shu_calculation
from shu.services.snapshot import aggregate_annual_weighting, backfill_snapshots
from users.models import UserProfile

FY_START = date(2025, 7, 1)
FY_END = date(2026, 6, 30)
SEED_RANGE_START = date(2014, 1, 1)

FIRST_NAMES = [
    "Jose", "Maria", "Joao", "Ana", "Domingos", "Filomena", "Francisco",
    "Aurora", "Antonio", "Rosa", "Manuel", "Lucia", "Carlos", "Teresa",
    "Abilio", "Marcelina", "Alberto", "Fatima", "Mario", "Ermelinda",
    "Julio", "Cristina", "Armindo", "Bernardina", "Cesar", "Delfina",
    "Egidio", "Felicidade", "Gil", "Herminia",
]
LAST_NAMES = [
    "Soares", "Martins", "Ximenes", "Belo", "Guterres", "Pereira",
    "da Costa", "Amaral", "Fernandes", "Gusmao", "Ribeiro", "Freitas",
    "Sarmento", "Correia", "Barreto", "Alves", "Marques", "Lopes",
    "Pinto", "de Araujo",
]
MUNICIPIOS = [
    "Dili", "Baucau", "Ainaro", "Same", "Maliana", "Suai", "Lospalos",
    "Liquica", "Aileu", "Ermera", "Viqueque", "Manatuto",
]
PROFESSIONS = [
    "Farmer", "Teacher", "Driver", "Market Vendor", "Fisherman",
    "Civil Servant", "Carpenter", "Shopkeeper", "Tailor", "Mechanic",
]


class Command(BaseCommand):
    help = (
        "Seed N members with multi-year join dates and realistic savings/"
        "loan history, then run a SHU calculation to test the dividend "
        "split's accuracy across members."
    )

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=150)
        parser.add_argument("--loan-pct", type=float, default=0.30)
        parser.add_argument("--seed", type=int, default=42)

    def handle(self, *args, **opts):
        random.seed(opts["seed"])
        count = opts["count"]

        maker, checker, certifier = self._staff()

        self._ensure_shu_split(maker, checker, certifier)

        self.stdout.write(f"Creating {count} members (2014–2026)…")
        members = self._create_members(count, maker, checker, certifier)

        self.stdout.write("Seeding savings history for the target FY…")
        self._seed_savings(members, maker, checker, certifier)

        n_loans = int(len(members) * opts["loan_pct"])
        loan_members = random.sample(members, k=n_loans)
        self.stdout.write(f"Seeding loans + repayments for {n_loans} members…")
        self._seed_loans(loan_members, maker, checker, certifier)

        self.stdout.write("Creating fiscal year and running SHU calculation…")
        fy = create_fiscal_year(FY_START, FY_END)
        n_snap = backfill_snapshots(fy)
        n_weight = aggregate_annual_weighting(fy)
        calc = run_shu_calculation(fy.id, maker_user=maker)

        payouts = calc.payouts.all()
        total_paid = sum((p.net_payout for p in payouts), Decimal("0"))

        self.stdout.write(self.style.SUCCESS("Done."))
        self.stdout.write(
            f"\nFiscal year {fy.year_start}–{fy.year_end}\n"
            f"  Net surplus:        {fy.net_surplus}\n"
            f"  Monthly snapshots:  {n_snap}\n"
            f"  Weighting rows:     {n_weight}\n"
            f"  SHU calculation:    {calc.id} [{calc.status}]\n"
            f"    reserva_legal:    {calc.reserva_legal_amt}\n"
            f"    admin_fund:       {calc.admin_fund_amt}\n"
            f"    jasa_simpanan:    {calc.jasa_simpanan_amt}\n"
            f"    jasa_bunga:       {calc.jasa_bunga_amt}\n"
            f"  Member payouts:     {payouts.count()} rows, "
            f"totaling {total_paid}\n"
            f"\nCalculation is PENDING_CHECK — check/certify it via the "
            f"Pipeline page (as checker1/certifier1, password changeme123) "
            f"to walk through payout and inspect per-member amounts."
        )

    # ----------------------------------------------------------------
    # Staff
    # ----------------------------------------------------------------
    def _staff(self):
        try:
            maker = UserProfile.objects.get(user__username="maker1")
            checker = UserProfile.objects.get(user__username="checker1")
            certifier = UserProfile.objects.get(user__username="certifier1")
        except UserProfile.DoesNotExist:
            raise CommandError(
                "maker1/checker1/certifier1 not found — run `manage.py "
                "bootstrap` first."
            ) from None
        return maker, checker, certifier

    # ----------------------------------------------------------------
    # Governance
    # ----------------------------------------------------------------
    def _ensure_shu_split(self, maker, checker, certifier):
        if GlobalConfig.objects.filter(
            parameter_key="shu_split", status="ACTIVE"
        ).exists():
            return
        change = propose_change(
            parameter_key="shu_split",
            proposed_value={
                "reserva_legal_pct": 25,
                "admin_fund_pct": 25,
                "jasa_simpanan_pct": 25,
                "jasa_bunga_pct": 25,
            },
            effective_from=SEED_RANGE_START,
            maker_user=maker,
        )
        pcheck(change.pipeline_actor, checker)
        pcertify(change.pipeline_actor, certifier)

    # ----------------------------------------------------------------
    # Members
    # ----------------------------------------------------------------
    def _random_join_date(self) -> date:
        """Skewed toward recent years — a growing cooperative."""
        years = list(range(SEED_RANGE_START.year, FY_END.year + 1))
        weights = [y - SEED_RANGE_START.year + 1 for y in years]
        year = random.choices(years, weights=weights, k=1)[0]
        start_of_year = date(year, 1, 1)
        end_of_year = date(year, 12, 31) if year != FY_END.year else FY_END
        offset = random.randint(0, (end_of_year - start_of_year).days)
        return start_of_year + timedelta(days=offset)

    def _create_members(self, count, maker, checker, certifier):
        members = []
        for i in range(count):
            join_date = self._random_join_date()
            member = Member.objects.create(
                salutation=random.choice(["Mr", "Mrs", "Ms"]),
                first_name=random.choice(FIRST_NAMES),
                last_name=random.choice(LAST_NAMES),
                national_id=f"TL{200000 + i}",
                phone_number=f"7{7000000 + i}",
                date_of_birth=date(
                    random.randint(1955, 2004), random.randint(1, 12),
                    random.randint(1, 28),
                ),
                aldeia=f"Aldeia {random.randint(1, 5)}",
                suco=f"Suco {random.randint(1, 10)}",
                posto=random.choice(MUNICIPIOS),
                municipio=random.choice(MUNICIPIOS),
                profession=random.choice(PROFESSIONS),
                status=Member.Status.PENDING,
                date_joined=join_date,
            )

            capital = Decimal(random.choice([50, 75, 100, 150, 200]))
            onboarding = pay_initial_capital(
                member=member, amount=capital, maker_user=maker,
                entry_date=join_date,
            )
            pcheck(onboarding.pipeline_actor, checker)
            pcertify(onboarding.pipeline_actor, certifier)
            member.refresh_from_db()
            members.append(member)

            if (i + 1) % 25 == 0:
                self.stdout.write(f"  …{i + 1}/{count} members onboarded")
        return members

    # ----------------------------------------------------------------
    # Savings
    # ----------------------------------------------------------------
    def _months_in_fy_from(self, start: date):
        y, m = start.year, start.month
        while date(y, m, 1) <= FY_END:
            day = min(5, [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
            yield date(y, m, day)
            m += 1
            if m == 13:
                m, y = 1, y + 1

    def _seed_savings(self, members, maker, checker, certifier):
        for idx, member in enumerate(members):
            start = max(member.date_joined, FY_START)
            if start > FY_END:
                continue

            voluntary_balance = Decimal("0")
            for month_date in self._months_in_fy_from(start):
                amount = Decimal(random.randint(10, 100))
                txn = deposit(
                    member=member, amount=amount, maker_user=maker,
                    entry_date=month_date,
                )
                pcheck(txn.pipeline_actor, checker)
                pcertify(txn.pipeline_actor, certifier)
                voluntary_balance += txn.voluntary_portion

                if random.random() < 0.15 and voluntary_balance > 20:
                    w_amount = (
                        voluntary_balance * Decimal(str(round(random.uniform(0.1, 0.3), 2)))
                    ).quantize(Decimal("0.01"))
                    if 0 < w_amount <= voluntary_balance:
                        wtxn = withdraw(
                            member=member, amount=w_amount, maker_user=maker,
                            entry_date=month_date + timedelta(days=3),
                        )
                        pcheck(wtxn.pipeline_actor, checker)
                        pcertify(wtxn.pipeline_actor, certifier)
                        voluntary_balance -= w_amount

            if (idx + 1) % 25 == 0:
                self.stdout.write(
                    f"  …savings seeded for {idx + 1}/{len(members)} members"
                )

    # ----------------------------------------------------------------
    # Loans
    # ----------------------------------------------------------------
    def _repayment_dates(self, n: int):
        span = (FY_END - FY_START).days
        step = span // (n + 1)
        return [FY_START + timedelta(days=step * (i + 1)) for i in range(n)]

    def _seed_loans(self, members, maker, checker, certifier):
        for idx, member in enumerate(members):
            principal = Decimal(random.choice([200, 300, 500, 800, 1000, 1500]))
            term = random.choice([6, 12, 24])
            rate = Decimal(str(random.choice(["0.01", "0.015", "0.02"])))

            loan = originate_loan(
                member=member, principal=principal, term_months=term,
                monthly_rate=rate, maker_user=maker,
                purpose="Working capital",
            )
            pcheck(loan.pipeline_actor, checker)
            pcertify(loan.pipeline_actor, certifier)
            loan.refresh_from_db()

            # Cosmetic only — the disbursement JE's real entry_date can't be
            # backdated (Loan itself isn't ledger-immutable, so this is safe;
            # it has no effect on SHU math, which only reads LoanRepayment).
            Loan.objects.filter(pk=loan.pk).update(
                disbursed_date=FY_START - timedelta(days=random.randint(10, 180))
            )

            n_repayments = random.randint(3, min(term, 10))
            scheduled_principal = (loan.principal_original / term).quantize(
                Decimal("0.01")
            )
            for pdate in self._repayment_dates(n_repayments):
                loan.refresh_from_db()
                if loan.status != Loan.Status.DISBURSED or loan.principal_outstanding <= 0:
                    break
                interest_due = (
                    loan.principal_outstanding * loan.monthly_rate
                ).quantize(Decimal("0.01"))
                principal_amt = min(scheduled_principal, loan.principal_outstanding)
                cash = interest_due + principal_amt

                rep = repay_scheduled(
                    loan=loan, cash_amount=cash, scheduled_principal=principal_amt,
                    payment_date=pdate, maker_user=maker,
                )
                pcheck(rep.pipeline_actor, checker)
                pcertify(rep.pipeline_actor, certifier)

            if (idx + 1) % 10 == 0:
                self.stdout.write(
                    f"  …loans seeded for {idx + 1}/{len(members)} members"
                )
