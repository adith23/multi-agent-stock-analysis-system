from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Shared Kernel"

    def ready(self) -> None:
        # Import after Django's split settings are fully evaluated. Importing
        # from config.__init__ would freeze base settings before test or
        # environment-specific overrides are applied.
        from apps.core.signals import structured_logging  # noqa: F401
        from config.celery import app as celery_app

        self.celery_app = celery_app
