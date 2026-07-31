"""
Development settings.
"""
from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "web", "nginx"])

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
    ],
)

# Friendlier local API browsing
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
}

# Email: SMTP via .env (fallback console if no credentials)
if not EMAIL_HOST_USER:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Optional: run Celery tasks synchronously when Redis is down locally
# CELERY_TASK_ALWAYS_EAGER = True

INTERNAL_IPS = ["127.0.0.1"]
