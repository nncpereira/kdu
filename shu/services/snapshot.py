from datetime import date
import calendar
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from ledger.services import account_net_balance
from members.models import Member
from shu.models import (
    ShuFiscalYear,
    ShuMemberMonthlyBalance,
    ShuWeightingBase,
)
from shu.services.eligibility import eligible_months, compute_weighted_units

KAPITAL_SOSIAL = "3101"
VOLUNTARY_DEPOSIT = "2101"


def _member_total_savings(member, as_of) -> Decimal:
    kapital = account_net_balance(KAPITAL_SOSIAL, member=member, as_of=as_of)
    voluntary = account_net_balance(VOLUNTARY_DEPOSIT, member=member, as_of=as_of)
    return kapital + voluntary


def _month_ends(start: date, end: date):
    y, m = start.year, start.month
    while True:
        last = date(y, m, calendar.monthrange(y, m)[1])
        if last > end:
            break
        if last >= start:
            yield last
        m += 1
        if m == 13:
            m, y = 1, y + 1


@transaction.atomic
def take_monthly_snapshot(snapshot_date: date = None, fy: ShuFiscalYear = None) -> int:
    """
    Snapshot every ACTIVE member's total savings as of `snapshot_date`.
    If `fy` is not provided, infer it from the date.
    """
    snapshot_date = snapshot_date or timezone.localdate()

    if fy is None:
        fy = ShuFiscalYear.objects.filter(
            year_start__lte=snapshot_date,
            year_end__gte=snapshot_date,
            status="OPEN",
        ).first()
    if not fy:
        return 0

    members = Member.objects.filter(status__in=["Active", "Dormant"])
    rows = 0
    for member in members.iterator():
        total = _member_total_savings(member, snapshot_date)
        if total <= 0:
            continue
        ShuMemberMonthlyBalance.objects.update_or_create(
            fy=fy,
            member=member,
            month_date=snapshot_date,
            defaults={"total_balance": total},
        )
        rows += 1
    return rows


@transaction.atomic
def backfill_snapshots(fy: ShuFiscalYear) -> int:
    """Run a snapshot for every month-end in the fiscal year range."""
    total = 0
    for month_end in _month_ends(fy.year_start, fy.year_end):
        total += take_monthly_snapshot(snapshot_date=month_end, fy=fy)
    return total


@transaction.atomic
def aggregate_annual_weighting(fy: ShuFiscalYear) -> int:
    """Recompute the per-member weighting base for a fiscal year."""
    from loans.models import LoanRepayment
    from django.db.models import Sum

    ShuWeightingBase.objects.filter(fy=fy).delete()

    member_ids = (
        ShuMemberMonthlyBalance.objects.filter(fy=fy)
        .values_list("member_id", flat=True)
        .distinct()
    )
    members = Member.objects.filter(id__in=list(member_ids))

    rows = 0
    for member in members:
        snapshots = {
            s.month_date: s.total_balance
            for s in ShuMemberMonthlyBalance.objects.filter(fy=fy, member=member)
        }
        weights_by_month = eligible_months(
            member.date_joined, fy.year_start, fy.year_end
        )

        month_balances = {}
        for month_end, weight in weights_by_month.items():
            if month_end in snapshots:
                month_balances[month_end] = (snapshots[month_end], weight)

        if not month_balances:
            continue

        sum_weighted, units = compute_weighted_units(month_balances)

        interest_paid = LoanRepayment.objects.filter(
            loan__member=member,
            status=LoanRepayment.Status.COMPLETED,
            payment_date__gte=fy.year_start,
            payment_date__lte=fy.year_end,
        ).aggregate(t=Sum("interest_paid"))["t"] or Decimal("0")

        ShuWeightingBase.objects.create(
            fy=fy,
            member=member,
            sum_weighted_balance=sum_weighted,
            months_active=len(month_balances),
            weighted_savings_units=units,
            loan_interest_paid=interest_paid,
        )
        rows += 1
    return rows
