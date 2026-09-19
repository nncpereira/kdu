from pipeline.summaries import register_summary


@register_summary("SHU_CALCULATE")
def _shu_calc(calc_id):
    from shu.models import ShuCalculation

    c = ShuCalculation.objects.select_related("fy").get(id=calc_id)
    return {
        "label": (
            f"SHU {c.fy.year_start}–{c.fy.year_end} — " f"Net surplus ${c.net_surplus}"
        ),
        "kind": "SHU_CALCULATE",
        "fiscal_year": f"{c.fy.year_start}–{c.fy.year_end}",
        "net_surplus": str(c.net_surplus),
        "reserva_legal_amt": str(c.reserva_legal_amt),
        "admin_fund_amt": str(c.admin_fund_amt),
        "jasa_simpanan_amt": str(c.jasa_simpanan_amt),
        "jasa_bunga_amt": str(c.jasa_bunga_amt),
    }
