"""Testing settings — fast, isolated test execution."""
from .base import *  # noqa: F401, F403

DEBUG = False

# Use a separate Neon branch for testing, or a local PostgreSQL
# Neon supports database branching — create a 'test' branch in the dashboard
DATABASES["default"] = env.db(
    "TEST_DATABASE_URL",
    default=DATABASES["default"],
)

# Faster password hashing for tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Disable Celery during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
