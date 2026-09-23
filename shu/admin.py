from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from shu.models import (
    ShuCalculation,
    ShuFiscalYear,
    ShuMemberMonthlyBalance,
    ShuMemberPayout,
    ShuWeightingBase,
)


@admin.register(ShuFiscalYear)
class ShuFiscalYearAdmin(admin.ModelAdmin):
    list_display = ("year_start", "year_end", "status", "net_surplus", "kapital_sosial")
    list_filter = ("status",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(ShuCalculation)
class ShuCalculationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "fy",
        "net_surplus",
        "total_allocated",
        "status",
        "reserve_journal_link",
    )
    list_filter = ("status", "fy")
    readonly_fields = (
        "id",
        "fy",
        "net_surplus",
        "reserva_legal_pct",
        "admin_fund_pct",
        "jasa_simpanan_pct",
        "jasa_bunga_pct",
        "reserva_legal_amt",
        "admin_fund_amt",
        "jasa_simpanan_amt",
        "jasa_bunga_amt",
        "status",
        "pipeline_actor",
        "reserve_journal_entry",
        "created_at",
        "updated_at",
    )

    def reserve_journal_link(self, obj):
        if not obj.reserve_journal_entry_id:
            return "—"
        url = reverse(
            "admin:ledger_journalentry_change", args=[obj.reserve_journal_entry_id]
        )
        return format_html('<a href="{}">{}</a>', url, obj.reserve_journal_entry_id)

    reserve_journal_link.short_description = "Reserve JE"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ShuMemberPayout)
class ShuMemberPayoutAdmin(admin.ModelAdmin):
    list_display = (
        "member",
        "calc",
        "jasa_simpanan_gross",
        "jasa_bunga_gross",
        "net_payout",
        "status",
    )
    list_filter = ("status",)
    search_fields = ("member__membership_number",)
    readonly_fields = (
        "id",
        "calc",
        "member",
        "jasa_simpanan_gross",
        "jasa_bunga_gross",
        "net_payout",
        "journal_entry",
        "status",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(ShuMemberMonthlyBalance)
admin.site.register(ShuWeightingBase)
