"""Shared Django settings.

Environment-specific policy belongs in ``development.py``, ``testing.py``, or
``production.py``. Secrets are never hard-coded here.
"""

from __future__ import annotations

import ssl
from datetime import timedelta
from pathlib import Path

import environ
import structlog
from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = BASE_DIR.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000"]),
)

backend_env = BASE_DIR / ".env"
root_env = PROJECT_DIR / ".env"

if backend_env.exists():
    env.read_env(backend_env)
elif root_env.exists():
    env.read_env(root_env)

SECRET_KEY = env("DJANGO_SECRET_KEY", default="unsafe-local-development-key")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1"],
)

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "guardian",
    "auditlog",
    "django_celery_beat",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.core",
    "apps.users",
    "apps.audit",
    "apps.market_data",
    "apps.data_ingestion",
    "apps.research",
    "apps.signals",
    "apps.risk_compliance",
    "apps.portfolio",
    "apps.orchestrator",
    "apps.api",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.tracing.RequestTracingMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
    "apps.core.middleware.audit.AuditLoggingMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASE_URL = env(
    "DATABASE_URL",
    default="postgresql://stockanalysis:stockanalysis@localhost:5432/stockanalysis",
)
DATABASES = {"default": env.db_url_config(DATABASE_URL)}
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = 60
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]
ANONYMOUS_USER_NAME = None

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT": 300,
        "KEY_PREFIX": "stockanalysis",
    }
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env(
    "CELERY_RESULT_BACKEND",
    default="redis://localhost:6379/2",
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 600
CELERY_TASK_SOFT_TIME_LIMIT = 540
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BEAT_SCHEDULE = {
    "ingest-enabled-market-sources-hourly": {
        "task": "apps.data_ingestion.tasks.ingest_enabled_sources",
        "schedule": 3600.0,
        "kwargs": {"categories": ["quote", "ohlcv", "news"]},
    },
    "ingest-enabled-reference-sources-daily": {
        "task": "apps.data_ingestion.tasks.ingest_enabled_sources",
        "schedule": 86400.0,
        "kwargs": {
            "categories": [
                "company_profile",
                "financial_statement",
                "filing",
                "ownership",
                "peer_group",
                "macro",
            ]
        },
    },
    "monitor-active-exit-triggers": {
        "task": "apps.portfolio.tasks.monitor_exit_triggers",
        "schedule": 300.0,
    },
    "monitor-active-catalysts": {
        "task": "apps.portfolio.tasks.monitor_catalysts",
        "schedule": 3600.0,
    },
    "track-recommendation-performance": {
        "task": "apps.portfolio.tasks.track_recommendation_performance",
        "schedule": 86400.0,
    },
    "expire-pm-reviews": {
        "task": "apps.portfolio.tasks.expire_pm_reviews",
        "schedule": 300.0,
    },
}
if CELERY_BROKER_URL.startswith("rediss://"):
    CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": ssl.CERT_REQUIRED}
if CELERY_RESULT_BACKEND.startswith("rediss://"):
    CELERY_REDIS_BACKEND_USE_SSL = {"ssl_cert_reqs": ssl.CERT_REQUIRED}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "apps.api.pagination.StandardResultsSetPagination",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "PAGE_SIZE": env.int("API_PAGE_SIZE", default=25),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "50/hour",
        "user": "500/hour",
        "analysis": "20/hour",
        "scenario": "30/hour",
        "pm_review": "60/hour",
    },
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S.%fZ",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Multi-Agent Stock Analysis API",
    "DESCRIPTION": "Investment research decision-support platform API.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_NAME_OVERRIDES": {
        "ActionSignalEnum": "apps.core.domain.enums.ActionSignal.choices",
    },
}

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000"],
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (
    *default_headers,
    "idempotency-key",
)

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": ("django.contrib.auth.password_validation.UserAttributeSimilarityValidator")},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
ML_MODEL_DIR = env("ML_MODEL_DIR", default=str(PROJECT_DIR / "ml_models"))

GOOGLE_API_KEY = env("GOOGLE_API_KEY", default="")
LLM_PROVIDER = env("LLM_PROVIDER", default="gemini")
LLM_DEFAULT_MODEL = env("LLM_DEFAULT_MODEL", default="gemini-3.1-flash-lite")
LLM_FALLBACK_MODEL = env("LLM_FALLBACK_MODEL", default="gemini-3.1-flash-lite")
LLM_TEMPERATURE = env.float("LLM_TEMPERATURE", default=0.3)
LLM_MAX_RETRIES = env.int("LLM_MAX_RETRIES", default=3)
LLM_REQUEST_TIMEOUT_SECONDS = env.int("LLM_REQUEST_TIMEOUT_SECONDS", default=60)

# External market-data credentials. They are read from the environment only;
# DataSourceConfiguration stores operational policy, never secret material.
FINNHUB_API_KEY = env("FINNHUB_API_KEY", default="")
FRED_API_KEY = env("FRED_API_KEY", default="")
NEWS_API_KEY = env("NEWS_API_KEY", default="")
ALPHA_VANTAGE_API_KEY = env("ALPHA_VANTAGE_API_KEY", default="")
SEC_EDGAR_IDENTITY = env("SEC_EDGAR_IDENTITY", default="")
TAVILY_API_KEY = env("TAVILY_API_KEY", default="")

LANGGRAPH_DATABASE_URL = env(
    "LANGGRAPH_DATABASE_URL",
    default=DATABASE_URL,
)

AUDIT_BODY_MAX_BYTES = env.int("AUDIT_BODY_MAX_BYTES", default=16_384)
AUDIT_EXCLUDED_PATH_PREFIXES = ("/static/",)
API_MAX_JSON_BYTES = env.int("API_MAX_JSON_BYTES", default=65_536)
API_MAX_JSON_DEPTH = env.int("API_MAX_JSON_DEPTH", default=8)
API_MAX_PAGE_SIZE = env.int("API_MAX_PAGE_SIZE", default=100)
ALLOW_API_AGENT_INPUT_OVERRIDES = env.bool(
    "ALLOW_API_AGENT_INPUT_OVERRIDES",
    default=False,
)
PM_REVIEW_TTL_HOURS = env.int("PM_REVIEW_TTL_HOURS", default=72)
DJANGO_STRUCTLOG_CELERY_ENABLED = True
DJANGO_STRUCTLOG_IP_LOGGING_ENABLED = False

LOG_LEVEL = env("LOG_LEVEL", default="INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": [
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso", utc=True),
            ],
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        }
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
