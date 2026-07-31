"""
Test settings (CI / pytest).
"""
from .base import *  # noqa: F401,F403

DEBUG = False

# Faster password hashing in tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# In-memory email
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Eager Celery (no Redis required for unit tests)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Prefer SQLite for isolated unit tests unless DATABASE_URL is forced
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
