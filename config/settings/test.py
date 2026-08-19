"""
Test settings (local pytest / GitHub Actions).
"""
import os

from .base import *  # noqa: F401,F403

DEBUG = False

# Faster password hashing in tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# In-memory email
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Eager Celery (no broker required for unit tests)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# GitHub Actions: use Postgres/Redis services. Locally: SQLite for speed.
if os.environ.get("GITHUB_ACTIONS") == "true":
    DATABASES = {
        "default": env.db("DATABASE_URL"),
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "test_db.sqlite3",
        }
    }

DATABASES["default"]["CONN_MAX_AGE"] = 0
DATABASES["default"]["CONN_HEALTH_CHECKS"] = False

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "apm-tests",
    }
}

# Disable shared caches in tests so assertions see fresh aggregates.
DASHBOARD_STATS_CACHE_TTL = 0
NOTIFICATION_BADGE_CACHE_TTL = 0

# Security middleware — permissif en tests
LOGIN_RATE_LIMIT_ENABLED = False
CONTENT_SECURITY_POLICY = ""
METRICS_ALLOWED_IPS = ["127.0.0.1", "::1", "testserver"]
