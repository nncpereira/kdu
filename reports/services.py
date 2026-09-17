from collections import defaultdict
from decimal import Decimal

from ledger.models import JournalTransactionLine
from accounting.models import Account


def _signed(entry_type: str, amount: Decimal) -> Decimal:
    """Return the signed value of a ledger line based on account type."""
    return amount if entry_type == "CREDIT" else -amount


def trial_balance(as_of):
    """
    Return a list of {account_code, account_name, account_type, debit, credit, net}
    for all accounts with movement up to `as_of`.
    """
    rows = defaultdict(lambda: {"debit": Decimal("0"), "credit": Decimal("0")})

    lines = JournalTransactionLine.objects.filter(
        journal_entry__entry_date__lte=as_of
    ).values_list("account_code", "entry_type", "amount")
    for code, entry_type, amount in lines:
        if entry_type == "DEBIT":
            rows[code]["debit"] += amount
        else:
            rows[code]["credit"] += amount

    accounts = {a.account_code: a for a in Account.objects.all()}
    result = []
    for code, data in rows.items():
        account = accounts.get(code)
        result.append(
            {
                "account_code": code,
                "account_name": account.account_name if account else code,
                "account_type": account.account_type if account else "",
                "debit": data["debit"],
                "credit": data["credit"],
                "net": data["debit"] - data["credit"],
            }
        )
    return sorted(result, key=lambda r: r["account_code"])


def income_statement(fy_start, fy_end):
    """
    Revenue (4xxx) minus Expenses (5xxx) for the period.
    Returns {"revenue": [...], "expenses": [...], "net_surplus": Decimal}.
    """
    rows = trial_balance(fy_end)
    revenue = [r for r in rows if r["account_code"].startswith("4")]
    expenses = [r for r in rows if r["account_code"].startswith("5")]

    total_revenue = sum((r["credit"] - r["debit"] for r in revenue), Decimal("0"))
    total_expenses = sum((r["debit"] - r["credit"] for r in expenses), Decimal("0"))

    return {
        "revenue": revenue,
        "expenses": expenses,
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_surplus": total_revenue - total_expenses,
    }


def balance_sheet(as_of):
    """
    Assets (1xxx) = Liabilities (2xxx) + Equity (3xxx).
    """
    rows = trial_balance(as_of)
    assets = [r for r in rows if r["account_code"].startswith("1")]
    liabilities = [r for r in rows if r["account_code"].startswith("2")]
    equity = [r for r in rows if r["account_code"].startswith("3")]

    total_assets = sum((r["net"] for r in assets), Decimal("0"))
    total_liabilities = sum((-r["net"] for r in liabilities), Decimal("0"))
    total_equity = sum((-r["net"] for r in equity), Decimal("0"))

    return {
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity,
        "balanced": total_assets == (total_liabilities + total_equity),
    }


def surplus_distribution(fy_id):
    """
    Return the certified SHU calculation amounts for the fiscal year.
    """
    from shu.models import ShuCalculation

    calc = ShuCalculation.objects.filter(fy_id=fy_id).order_by("-created_at").first()
    if not calc:
        return None
    return {
        "reserva_legal_amt": calc.reserva_legal_amt,
        "admin_fund_amt": calc.admin_fund_amt,
        "jasa_simpanan_amt": calc.jasa_simpanan_amt,
        "jasa_bunga_amt": calc.jasa_bunga_amt,
        "status": calc.status,
    }
