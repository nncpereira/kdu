import importlib

from django.apps import AppConfig


class ExpensesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "expenses"

    def ready(self):
        importlib.import_module("expenses.handlers")
        importlib.import_module("expenses.summaries")
