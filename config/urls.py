"""URL configuration for APM Platform."""
from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from apps.core.protected_docs import (
    ProtectedSpectacularAPIView,
    ProtectedSpectacularRedocView,
    ProtectedSpectacularSwaggerView,
)
from apps.core.secure_media import SecureMediaView

admin.site.site_header = "Topnet APM — Administration"
admin.site.site_title = "Topnet APM"
admin.site.index_title = "Console d'administration"


def healthcheck(_request):
    """Lightweight liveness probe for Docker / load balancers."""
    return JsonResponse({"status": "ok", "service": "apm-platform"})


urlpatterns = [
    path("", include("django_prometheus.urls")),
    path("media/<path:path>", SecureMediaView.as_view(), name="secure-media"),
    path("", include("apps.accounts.urls_web")),
    path("", include("apps.applications.urls_web")),
    path("", include("apps.technologies.urls_web")),
    path("", include("apps.environments.urls_web")),
    path("", include("apps.servers.urls_web")),
    path("", include("apps.certificates.urls_web")),
    path("", include("apps.domains.urls_web")),
    path("", include("apps.vendors.urls_web")),
    path("", include("apps.contracts.urls_web")),
    path("", include("apps.documents.urls_web")),
    path("", include("apps.incidents.urls_web")),
    path("", include("apps.dependencies.urls_web")),
    path("", include("apps.notifications.urls_web")),
    path("", include("apps.audit.urls_web")),
    path("", include("apps.dashboard.urls_web")),
    path("admin/", admin.site.urls),
    path("api/health/", healthcheck, name="healthcheck"),
    # OpenAPI / Swagger (Admin DSI + session requise)
    path("api/schema/", ProtectedSpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        ProtectedSpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        ProtectedSpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # Auth + Users API (JWT)
    path("api/auth/", include("apps.accounts.urls")),
    # Domain APIs
    path("api/applications/", include("apps.applications.urls")),
    path("api/technologies/", include("apps.technologies.urls")),
    path("api/environments/", include("apps.environments.urls")),
    path("api/servers/", include("apps.servers.urls")),
    path("api/certificates/", include("apps.certificates.urls")),
    path("api/domains/", include("apps.domains.urls")),
    path("api/vendors/", include("apps.vendors.urls")),
    path("api/contracts/", include("apps.contracts.urls")),
    path("api/documents/", include("apps.documents.urls")),
    path("api/incidents/", include("apps.incidents.urls")),
    path("api/dependencies/", include("apps.dependencies.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
]

# Dev only: servir static source (media toujours via SecureMediaView)
if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
