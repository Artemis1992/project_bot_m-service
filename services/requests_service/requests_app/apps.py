from django.apps import AppConfig


class RequestsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "requests_app"
    verbose_name = "Служебные записки"

    def ready(self):
        """Import signals when app is ready."""
        import requests_app.signals  # noqa: F401

