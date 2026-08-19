"""Middleware sécurité : rate limit, headers, admin, métriques."""

from __future__ import annotations

import ipaddress

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseForbidden

from apps.accounts.roles import is_admin_dsi
from apps.core.rate_limit import is_rate_limited, register_rate_limit_attempt


def _client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or ""


def _is_private_or_loopback(ip: str) -> bool:
    if not ip:
        return False
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return addr.is_private or addr.is_loopback


class LoginRateLimitMiddleware:
    """Limite les tentatives POST sur login web, JWT et reset password."""

    SCOPED_PATHS = {
        "/login/": "web_login",
        "/api/auth/token/": "jwt_token",
        "/api/auth/token/refresh/": "jwt_refresh",
        "/password-reset/": "password_reset",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        scope = None
        if request.method == "POST":
            path = request.path
            scope = self.SCOPED_PATHS.get(path)

        if scope and is_rate_limited(request, scope=scope):
            return HttpResponse(
                "Trop de tentatives. Réessayez dans quelques minutes.",
                status=429,
                content_type="text/plain; charset=utf-8",
            )

        response = self.get_response(request)

        if not scope:
            return response

        if scope == "web_login":
            if response.status_code in {302, 303}:
                from apps.core.rate_limit import clear_rate_limit

                clear_rate_limit(request, scope=scope)
            elif response.status_code == 200:
                register_rate_limit_attempt(request, scope=scope)
        elif scope in {"jwt_token", "jwt_refresh"}:
            if response.status_code == 200:
                from apps.core.rate_limit import clear_rate_limit

                clear_rate_limit(request, scope=scope)
            elif response.status_code in {401, 400}:
                register_rate_limit_attempt(request, scope=scope)
        elif scope == "password_reset":
            if response.status_code in {200, 302}:
                register_rate_limit_attempt(request, scope=scope)

        return response


class AdminAccessMiddleware:
    """Restreint /admin/ aux comptes Admin DSI (pas simple is_staff)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith("/admin/") and not path.startswith("/admin/login/"):
            user = getattr(request, "user", None)
            if user and user.is_authenticated and not is_admin_dsi(user):
                raise PermissionDenied
        return self.get_response(request)


class MetricsAccessMiddleware:
    """Protège /metrics (Prometheus) — IP privée, token ou Admin DSI."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.rstrip("/") != "/metrics":
            return self.get_response(request)

        token = getattr(settings, "METRICS_TOKEN", "") or ""
        header_token = request.headers.get("X-Metrics-Token", "")
        if token and header_token == token:
            return self.get_response(request)

        client_ip = _client_ip(request)
        allowed_ips = getattr(settings, "METRICS_ALLOWED_IPS", [])
        if client_ip in allowed_ips or _is_private_or_loopback(client_ip):
            return self.get_response(request)

        user = getattr(request, "user", None)
        if user and user.is_authenticated and is_admin_dsi(user):
            return self.get_response(request)

        return HttpResponseForbidden("Metrics access denied.")


class SecurityHeadersMiddleware:
    """CSP et headers complémentaires."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        csp = getattr(settings, "CONTENT_SECURITY_POLICY", "")
        if csp:
            response.headers.setdefault("Content-Security-Policy", csp)
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        return response
