import importlib

from django.apps import AppConfig


class LedgerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ledger"

    def ready(self):
        importlib.import_module("ledger.handlers")
        importlib.import_module("ledger.summaries")
