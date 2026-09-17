from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from expenses.models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "description",
        "amount",
        "expense_account_code",
        "status",
        "payment_date",
        "journal_entry_link",
    )
    list_filter = ("status", "expense_account_code", "payment_date")
    search_fields = ("description", "expense_account_code")
    readonly_fields = (
        "id",
        "journal_entry",
        "pipeline_actor",
        "status",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Details",
            {
                "fields": (
                    "id",
                    "description",
                    "amount",
                    "expense_account_code",
                    "payment_date",
                )
            },
        ),
        ("Workflow", {"fields": ("status", "pipeline_actor", "journal_entry")}),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )

    def journal_entry_link(self, obj):
        if not obj.journal_entry_id:
            return "—"
        url = reverse("admin:ledger_journalentry_change", args=[obj.journal_entry_id])
        return format_html('<a href="{}">{}</a>', url, obj.journal_entry_id)

    journal_entry_link.short_description = "Journal Entry"

    def has_delete_permission(self, request, obj=None):
        return False
