import importlib

from django.apps import AppConfig


class SavingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "savings"

    def ready(self):
        importlib.import_module("savings.handlers")
        importlib.import_module("savings.summaries")
