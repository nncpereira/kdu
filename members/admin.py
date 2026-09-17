from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from members.models import Member, MemberOnboarding, MemberExitRequest


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        "membership_number",
        "full_name",
        "status",
        "kapital_sosial_balance",
        "date_joined",
    )
    list_filter = ("status", "municipio", "date_joined")
    search_fields = ("membership_number", "first_name", "last_name", "phone_number")
    readonly_fields = (
        "id",
        "membership_number",
        "kapital_sosial_balance",
        "created_at",
        "updated_at",
        "last_transaction_at",
    )
    fieldsets = (
        (
            "Identity",
            {
                "fields": (
                    "id",
                    "membership_number",
                    "salutation",
                    "first_name",
                    "middle_name",
                    "last_name",
                    "date_of_birth",
                )
            },
        ),
        ("Contact", {"fields": ("phone_number", "email", "national_id")}),
        ("Address", {"fields": ("aldeia", "suco", "posto", "municipio")}),
        (
            "Membership",
            {
                "fields": (
                    "profession",
                    "status",
                    "date_joined",
                    "kapital_sosial_balance",
                    "user",
                    "last_transaction_at",
                )
            },
        ),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )

    def has_delete_permission(self, request, obj=None):
        return False  # never delete members


@admin.register(MemberOnboarding)
class MemberOnboardingAdmin(admin.ModelAdmin):
    list_display = (
        "member",
        "initial_capital_amount",
        "status",
        "journal_entry_link",
        "created_at",
    )
    list_filter = ("status",)
    readonly_fields = (
        "id",
        "member",
        "initial_capital_amount",
        "journal_entry",
        "pipeline_actor",
        "status",
        "created_at",
        "updated_at",
    )

    def journal_entry_link(self, obj):
        if not obj.journal_entry_id:
            return "—"
        url = reverse("admin:ledger_journalentry_change", args=[obj.journal_entry_id])
        return format_html('<a href="{}">{}</a>', url, obj.journal_entry_id)

    journal_entry_link.short_description = "Journal Entry"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MemberExitRequest)
class MemberExitRequestAdmin(admin.ModelAdmin):
    list_display = (
        "member",
        "refund_amount",
        "status",
        "journal_entry_link",
        "created_at",
    )
    list_filter = ("status",)
    readonly_fields = (
        "id",
        "member",
        "refund_amount",
        "journal_entry",
        "pipeline_actor",
        "status",
        "created_at",
        "updated_at",
    )

    def journal_entry_link(self, obj):
        if not obj.journal_entry_id:
            return "—"
        url = reverse("admin:ledger_journalentry_change", args=[obj.journal_entry_id])
        return format_html('<a href="{}">{}</a>', url, obj.journal_entry_id)

    journal_entry_link.short_description = "Journal Entry"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
