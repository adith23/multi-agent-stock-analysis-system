"""
Base Django settings for the Multi-Agent Stock Analysis System.

Reference: SYSTEM_ARCHITECTURE_AND_DESIGN.md §3, §7, §9
"""

import os
from pathlib import Path
from datetime import timedelta

import environ

# ============================================
# Path & Environment Setup
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost"]),
)

# Read .env file from project root (one level above backend/)
ENV_FILE = BASE_DIR.parent / ".env"
if ENV_FILE.exists():
    env.read_env(str(ENV_FILE))

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# ============================================
# Application Definition
# ============================================
DJANGO_APPS = [
    "daphne",  # Must be before django.contrib.staticfiles for ASGI
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "channels",
    "django_celery_beat",
    "django_celery_results",
]

LOCAL_APPS = [
    "apps.core",
    "apps.ingestion",
    "apps.signals",
    "apps.agents",
    "apps.pipeline",
    "apps.risk",
    "apps.portfolio",
    "apps.review",
    "apps.audit",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ============================================
# Middleware
# ============================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ============================================
# Database — Neon Serverless PostgreSQL
# ============================================
# Neon requires SSL. Use DATABASE_URL for simplicity,
# or individual env vars for granular control.
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgresql://localhost:5432/stockanalysis",
    ),
}

# Neon requires SSL connections
DATABASES["default"]["OPTIONS"] = {
    "sslmode": "require",
    "connect_timeout": 10,
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ============================================
# MongoDB Atlas (via Motor/PyMongo — not through Django ORM)
# ============================================
# Atlas uses mongodb+srv:// connection strings with TLS by default.
MONGODB_URL = env("MONGODB_URL", default="mongodb://localhost:27017/stockanalysis")
MONGODB_DB_NAME = env("MONGODB_DB", default="stockanalysis")

# ============================================
# Redis Cloud
# ============================================
# Redis Cloud uses rediss:// (TLS). Free tier = 1 database (no /0, /1 numbering).
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# ============================================
# Django Channels (WebSocket via Redis)
# ============================================
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379/0")],
        },
    },
}

# ============================================
# Confluent Cloud Kafka
# ============================================
KAFKA_BOOTSTRAP_SERVERS = env("KAFKA_BOOTSTRAP_SERVERS", default="localhost:9092")
KAFKA_SECURITY_PROTOCOL = env("KAFKA_SECURITY_PROTOCOL", default="PLAINTEXT")
KAFKA_SASL_MECHANISM = env("KAFKA_SASL_MECHANISM", default="PLAIN")
KAFKA_SASL_USERNAME = env("KAFKA_SASL_USERNAME", default="")
KAFKA_SASL_PASSWORD = env("KAFKA_SASL_PASSWORD", default="")

# ============================================
# Celery Configuration
# ============================================
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 600  # 10 minutes max per task
CELERY_TASK_SOFT_TIME_LIMIT = 540  # Soft limit at 9 minutes
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_RESULT_EXTENDED = True

# ============================================
# Django REST Framework
# ============================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "50/hour",
        "user": "500/hour",
    },
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S.%fZ",
    "DATE_FORMAT": "%Y-%m-%d",
}

# ============================================
# JWT Configuration
# ============================================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ============================================
# CORS Configuration
# ============================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Next.js frontend
]
CORS_ALLOW_CREDENTIALS = True

# ============================================
# Password Validation
# ============================================
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ============================================
# Internationalization
# ============================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ============================================
# Static Files
# ============================================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ============================================
# LLM Configuration
# ============================================
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")

# Default LLM settings per agent (can be overridden via agent_configs table)
LLM_DEFAULTS = {
    "model": "gpt-4o-mini",
    "temperature": 0,
    "max_tokens": 4096,
    "request_timeout": 60,
}

# ============================================
# Data Source Configuration
# ============================================
DATA_SOURCES = {
    "FRED_API_KEY": env("FRED_API_KEY", default=""),
    "ALPHA_VANTAGE_API_KEY": env("ALPHA_VANTAGE_API_KEY", default=""),
    "NEWS_API_KEY": env("NEWS_API_KEY", default=""),
}

# ============================================
# Logging (Structured JSON via structlog)
# ============================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": "structlog.dev.ConsoleRenderer",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}
