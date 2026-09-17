from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from datetime import date

from ledger.services import account_net_balance
from members.models import Member
from shu.models import ShuFiscalYear, ShuMemberMonthlyBalance, ShuWeightingBase
from shu.services.eligibility import eligible_months, compute_weighted_units

KAPITAL_SOSIAL = "3101"
VOLUNTARY_DEPOSIT = "2101"


# ====================================================================
# Monthly snapshot
# ====================================================================
def _member_total_savings(member, as_of) -> Decimal:
    """Total savings = Kapital Sosial + Voluntary Deposits at a given date."""
    kapital = account_net_balance(KAPITAL_SOSIAL, member=member, as_of=as_of)
    voluntary = account_net_balance(VOLUNTARY_DEPOSIT, member=member, as_of=as_of)
    return kapital + voluntary


@transaction.atomic
def take_monthly_snapshot(snapshot_date: date = None) -> int:
    """
    Snapshot every ACTIVE member's total savings as of `snapshot_date`
    (defaults to today). Idempotent: re-running overwrites the same
    (fy, member, month) row.
    """
    snapshot_date = snapshot_date or timezone.localdate()

    fy = ShuFiscalYear.objects.filter(
        year_start__lte=snapshot_date, year_end__gte=snapshot_date, status="OPEN"
    ).first()
    if not fy:
        # Fall back to most recent open FY if snapshot is exactly at boundary
        fy = ShuFiscalYear.objects.filter(status="OPEN").order_by("-year_start").first()
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


# ====================================================================
# Annual aggregation
# ====================================================================
@transaction.atomic
def aggregate_annual_weighting(fy: ShuFiscalYear) -> int:
    """
    Compute per-member weighting base for a fiscal year.
    Uses the monthly snapshots and the certified loan interest.
    Idempotent: replaces existing rows for the FY.
    """
    from loan_repayments_aggregator import sum_interest_paid  # see below

    ShuWeightingBase.objects.filter(fy=fy).delete()

    members = Member.objects.filter(shu_monthly_balances__fy=fy).distinct()

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
        months_active = len(month_balances)
        interest_paid = sum_interest_paid(member, fy.year_start, fy.year_end)

        ShuWeightingBase.objects.create(
            fy=fy,
            member=member,
            sum_weighted_balance=sum_weighted,
            months_active=months_active,
            weighted_savings_units=units,
            loan_interest_paid=interest_paid,
        )
        rows += 1
    return rows


# ====================================================================
# Helper: total certified interest paid by a member
# ====================================================================
def _sum_interest_paid(member, start, end) -> Decimal:
    from loans.models import LoanRepayment
    from django.db.models import Sum

    total = LoanRepayment.objects.filter(
        loan__member=member,
        status=LoanRepayment.Status.COMPLETED,
        payment_date__gte=start,
        payment_date__lte=end,
    ).aggregate(t=Sum("interest_paid"))["t"] or Decimal("0")
    return total


# Expose as module-level for the import above
sum_interest_paid = _sum_interest_paid
