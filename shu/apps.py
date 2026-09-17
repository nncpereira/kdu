from django.apps import AppConfig


class ShuConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shu"

    def ready(self):
        # Register pipeline handlers on app load.
        from shu import handlers
