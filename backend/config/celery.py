"""
Celery application configuration.

Reference: SYSTEM_ARCHITECTURE_AND_DESIGN.md §6
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("stockanalysis")

# Load config from Django settings, using the CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Test task to verify Celery is working."""
    print(f"Request: {self.request!r}")
