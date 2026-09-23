import importlib

from django.apps import AppConfig


class ShuConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shu"

    def ready(self):
        importlib.import_module("shu.handlers")
        importlib.import_module("shu.summaries")
