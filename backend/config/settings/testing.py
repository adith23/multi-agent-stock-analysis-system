"""Fast, deterministic test settings."""

import os

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-only-secret-key-at-least-thirty-two-bytes"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

TEST_DATABASE_URL = env(  # noqa: F405
    "TEST_DATABASE_URL",
    default=f"sqlite:///{BASE_DIR / 'test.sqlite3'}",  # noqa: F405
)
DATABASES = {"default": env.db_url_config(TEST_DATABASE_URL)}  # noqa: F405

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "stockanalysis-tests",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# Celery gives process environment variables precedence over Django settings.
# Replace values loaded from a developer .env so tests can never contact Redis.
os.environ["CELERY_BROKER_URL"] = CELERY_BROKER_URL
os.environ["CELERY_RESULT_BACKEND"] = CELERY_RESULT_BACKEND
