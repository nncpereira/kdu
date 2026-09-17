from django.contrib import admin

# Register your models here.
from django.contrib import admin
from ledger.models import JournalEntry, JournalTransactionLine


class JournalTransactionLineInline(admin.TabularInline):
    model = JournalTransactionLine
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("account_code", "member", "entry_type", "amount")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        # Only allow adding lines while the entry is in DRAFT.
        if obj and obj.status == JournalEntry.Status.CERTIFIED:
            return False
        return super().has_add_permission(request, obj)


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "entry_date",
        "description",
        "status",
        "total_debits",
        "total_credits",
        "is_balanced",
    )
    list_filter = ("status", "entry_date")
    search_fields = ("description", "id")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "certified_by",
        "original_journal_entry",
        "total_debits",
        "total_credits",
        "is_balanced",
    )
    inlines = [JournalTransactionLineInline]

    def has_delete_permission(self, request, obj=None):
        # Never allow deletion of journal entries.
        return False

    def has_change_permission(self, request, obj=None):
        # Certified entries are read-only.
        if obj and obj.status == JournalEntry.Status.CERTIFIED:
            return False
        return super().has_change_permission(request, obj)
