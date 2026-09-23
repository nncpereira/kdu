import importlib

from django.apps import AppConfig


class MembersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "members"

    def ready(self):
        # Importing these modules registers the @register handlers and
        # @receiver signal receivers. Do not remove — ruff and friends
        # see them as unused, but the side effect is what matters.
        importlib.import_module("members.handlers")
        importlib.import_module("members.summaries")
