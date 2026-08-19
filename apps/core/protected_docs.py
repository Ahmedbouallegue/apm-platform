"""Swagger / OpenAPI réservés aux Admin DSI."""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.accounts.decorators import user_passes_test_or_403
from apps.accounts.roles import is_admin_dsi


def _admin_dsi_required(view_cls):
    return method_decorator(login_required, name="dispatch")(
        method_decorator(user_passes_test_or_403(is_admin_dsi), name="dispatch")(view_cls)
    )


@_admin_dsi_required
class ProtectedSpectacularAPIView(SpectacularAPIView):
    pass


@_admin_dsi_required
class ProtectedSpectacularSwaggerView(SpectacularSwaggerView):
    pass


@_admin_dsi_required
class ProtectedSpectacularRedocView(SpectacularRedocView):
    pass
