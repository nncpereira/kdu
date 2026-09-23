import importlib

from django.apps import AppConfig


class LoansConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "loans"

    def ready(self):
        importlib.import_module("loans.handlers")
        importlib.import_module("loans.summaries")
