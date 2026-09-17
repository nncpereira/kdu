# savings/admin.py
from django.contrib import admin
from savings.models import Transaction, MemberVoluntaryDeposit


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "member",
        "transaction_type",
        "requested_amount",
        "obligatory_portion",
        "voluntary_portion",
        "status",
        "created_at",
    )
    list_filter = ("transaction_type", "status")
    search_fields = ("member__membership_number", "id")
    readonly_fields = (
        "id",
        "pipeline_actor",
        "journal_entry",
        "created_at",
        "updated_at",
    )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MemberVoluntaryDeposit)
class MemberVoluntaryDepositAdmin(admin.ModelAdmin):
    list_display = (
        "member",
        "balance_available",
        "balance_held_pipeline",
        "updated_at",
    )
    search_fields = ("member__membership_number",)
    readonly_fields = (
        "member",
        "balance_available",
        "balance_held_pipeline",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False  # read-only; balances managed by ledger signal

    def has_delete_permission(self, request, obj=None):
        return False
