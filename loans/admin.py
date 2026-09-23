# loans/admin.py
from django.contrib import admin

from loans.models import Loan, LoanRepayment


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "member",
        "principal_original",
        "principal_outstanding",
        "monthly_rate",
        "term_months",
        "status",
        "disbursed_date",
    )
    list_filter = ("status",)
    search_fields = ("member__membership_number", "id")
    readonly_fields = (
        "id",
        "principal_original",
        "principal_outstanding",
        "status",
        "disbursed_date",
        "pipeline_actor",
        "journal_entry",
        "created_at",
        "updated_at",
    )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "loan",
        "principal_paid",
        "interest_paid",
        "payment_date",
        "mode",
        "status",
    )
    list_filter = ("status", "mode", "payment_date")
    readonly_fields = (
        "id",
        "loan",
        "principal_paid",
        "interest_paid",
        "payment_date",
        "mode",
        "status",
        "pipeline_actor",
        "journal_entry",
        "created_at",
        "updated_at",
    )

    def has_delete_permission(self, request, obj=None):
        return False
