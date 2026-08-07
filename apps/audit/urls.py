from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.audit.views.api import AuditLogViewSet, HealthView

router = DefaultRouter()
router.register("", AuditLogViewSet, basename="auditlog")

urlpatterns = [
    path("health/", HealthView.as_view(), name="audit-health"),
    *router.urls,
]
