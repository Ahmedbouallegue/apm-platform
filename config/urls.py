"""URL configuration for APM Platform."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

admin.site.site_header = "Topnet APM — Administration"
admin.site.site_title = "Topnet APM"
admin.site.index_title = "Console d'administration"


def healthcheck(_request):
    """Lightweight liveness probe for Docker / load balancers."""
    return JsonResponse({"status": "ok", "service": "apm-platform"})


urlpatterns = [
    path("", include("django_prometheus.urls")),
    path("", include("apps.accounts.urls_web")),
    path("admin/", admin.site.urls),
    path("api/health/", healthcheck, name="healthcheck"),
    # OpenAPI / Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # Auth + Users API (JWT)
    path("api/auth/", include("apps.accounts.urls")),
    # Domain APIs (stubs — filled in later sprints)
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

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
