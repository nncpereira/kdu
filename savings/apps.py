from django.apps import AppConfig


class SavingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "savings"

    def ready(self):
        # Import handlers so their @register decorators run.
        from savings import handlers
        from savings import summaries
