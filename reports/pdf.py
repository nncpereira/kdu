"""
Render report HTML templates to PDF using WeasyPrint.
"""

from decimal import Decimal
from io import BytesIO

from django.template.loader import render_to_string
from django.utils import timezone


def _fmt_money(value) -> str:
    """Format a Decimal or string as '1,234.56'."""
    if value is None:
        return "0.00"
    d = Decimal(str(value))
    # Use Python's format spec for thousands separators.
    return f"{d:,.2f}"


def _fmt_date(value) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%d %B %Y")
    return str(value)


def render_pdf(template_name: str, context: dict) -> bytes:
    """
    Render the given template with the context and return PDF bytes.
    """
    from weasyprint import HTML

    context.setdefault("generated_at", timezone.now().strftime("%d/%m/%Y %H:%M"))
    html = render_to_string(template_name, context)
    pdf_bytes = HTML(string=html).write_pdf()
    return pdf_bytes


# ====================================================================
# Per-report builders
# ====================================================================
def build_trial_balance_pdf(as_of) -> bytes:
    from reports.services import trial_balance

    rows = trial_balance(as_of)
    total_debit = sum((Decimal(str(r["debit"])) for r in rows), Decimal("0"))
    total_credit = sum((Decimal(str(r["credit"])) for r in rows), Decimal("0"))
    balanced = abs(total_debit - total_credit) < Decimal("0.01")

    # Format for display
    display_rows = [
        {
            "account_code": r["account_code"],
            "account_name": r["account_name"],
            "account_type": r["account_type"],
            "debit": _fmt_money(r["debit"]),
            "credit": _fmt_money(r["credit"]),
            "net": _fmt_money(r["net"]),
        }
        for r in rows
    ]

    return render_pdf(
        "reports/trial_balance.html",
        {
            "title": "Trial Balance",
            "period": f"As of {_fmt_date(as_of)}",
            "rows": display_rows,
            "total_debit": _fmt_money(total_debit),
            "total_credit": _fmt_money(total_credit),
            "balanced": balanced,
        },
    )


def build_income_statement_pdf(start, end) -> bytes:
    from reports.services import income_statement

    data = income_statement(start, end)

    return render_pdf(
        "reports/income_statement.html",
        {
            "title": "Income Statement",
            "period": f"{_fmt_date(start)} to {_fmt_date(end)}",
            "revenue": [
                {**r, "credit": _fmt_money(r["credit"])} for r in data["revenue"]
            ],
            "expenses": [
                {**r, "debit": _fmt_money(r["debit"])} for r in data["expenses"]
            ],
            "total_revenue": _fmt_money(data["total_revenue"]),
            "total_expenses": _fmt_money(data["total_expenses"]),
            "net_surplus": _fmt_money(data["net_surplus"]),
        },
    )


def build_balance_sheet_pdf(as_of) -> bytes:
    from reports.services import balance_sheet

    data = balance_sheet(as_of)

    def liab_amount(r):
        return Decimal(str(r["credit"])) - Decimal(str(r["debit"]))

    def eq_amount(r):
        return Decimal(str(r["credit"])) - Decimal(str(r["debit"]))

    return render_pdf(
        "reports/balance_sheet.html",
        {
            "title": "Balance Sheet",
            "period": f"As of {_fmt_date(as_of)}",
            "assets": [{**r, "net": _fmt_money(r["net"])} for r in data["assets"]],
            "liabilities": [
                {**r, "liability_amount": _fmt_money(liab_amount(r))}
                for r in data["liabilities"]
            ],
            "equity": [
                {**r, "equity_amount": _fmt_money(eq_amount(r))} for r in data["equity"]
            ],
            "total_assets": _fmt_money(data["total_assets"]),
            "total_liabilities": _fmt_money(data["total_liabilities"]),
            "total_equity": _fmt_money(data["total_equity"]),
            "balanced": data["balanced"],
        },
    )


def build_surplus_distribution_pdf(fy_id) -> bytes:
    from shu.models import ShuCalculation, ShuFiscalYear

    fy = ShuFiscalYear.objects.get(pk=fy_id)
    calc = (
        ShuCalculation.objects.filter(fy=fy)
        .exclude(status="REJECTED")
        .order_by("-created_at")
        .first()
    )

    if not calc:
        # Render a stub PDF saying no calculation exists yet.
        return render_pdf(
            "reports/surplus_distribution.html",
            {
                "title": "Surplus Distribution",
                "period": f"Fiscal Year {_fmt_date(fy.year_start)} – {_fmt_date(fy.year_end)}",
                "reserva_legal_amt": "0.00",
                "admin_fund_amt": "0.00",
                "jasa_simpanan_amt": "0.00",
                "jasa_bunga_amt": "0.00",
                "status": "NOT_CALCULATED",
                "net_surplus": "0.00",
                "reserva_legal_pct": "0.00",
                "admin_fund_pct": "0.00",
                "jasa_simpanan_pct": "0.00",
                "jasa_bunga_pct": "0.00",
                "payouts": [],
                "total_payout": "0.00",
            },
        )

    payouts = list(
        calc.payouts.select_related("member").order_by("member__membership_number")
    )
    total_payout = sum((p.net_payout for p in payouts), Decimal("0"))

    display_payouts = [
        {
            "member_number": p.member.membership_number,
            "full_name": p.member.full_name,
            "jasa_simpanan_gross": _fmt_money(p.jasa_simpanan_gross),
            "jasa_bunga_gross": _fmt_money(p.jasa_bunga_gross),
            "net_payout": _fmt_money(p.net_payout),
        }
        for p in payouts
    ]

    return render_pdf(
        "reports/surplus_distribution.html",
        {
            "title": "Surplus Distribution (SHU)",
            "period": f"Fiscal Year {_fmt_date(fy.year_start)} – {_fmt_date(fy.year_end)}",
            "reserva_legal_amt": _fmt_money(calc.reserva_legal_amt),
            "admin_fund_amt": _fmt_money(calc.admin_fund_amt),
            "jasa_simpanan_amt": _fmt_money(calc.jasa_simpanan_amt),
            "jasa_bunga_amt": _fmt_money(calc.jasa_bunga_amt),
            "status": calc.status,
            "net_surplus": _fmt_money(calc.net_surplus),
            "reserva_legal_pct": _fmt_money(calc.reserva_legal_pct),
            "admin_fund_pct": _fmt_money(calc.admin_fund_pct),
            "jasa_simpanan_pct": _fmt_money(calc.jasa_simpanan_pct),
            "jasa_bunga_pct": _fmt_money(calc.jasa_bunga_pct),
            "payouts": display_payouts,
            "total_payout": _fmt_money(total_payout),
        },
    )
