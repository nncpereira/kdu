from django.contrib import admin
from governance.models import GlobalConfig, GlobalConfigChange


@admin.register(GlobalConfig)
class GlobalConfigAdmin(admin.ModelAdmin):
    list_display = ("parameter_key", "effective_from", "status", "created_at")
    list_filter = ("parameter_key", "status")
    readonly_fields = ("created_at", "updated_at")


@admin.register(GlobalConfigChange)
class GlobalConfigChangeAdmin(admin.ModelAdmin):
    list_display = ("parameter_key", "status", "effective_from", "created_at")
    list_filter = ("status", "parameter_key")
