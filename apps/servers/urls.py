from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.servers.views.api import (
    HealthView,
    ServerMetricIngestView,
    ServerMetricListView,
    ServerViewSet,
)

router = DefaultRouter()
router.register("", ServerViewSet, basename="server")

urlpatterns = [
    path("health/", HealthView.as_view(), name="servers-health"),
    path("metrics/", ServerMetricIngestView.as_view(), name="server-metrics-ingest"),
    path("metrics/list/", ServerMetricListView.as_view(), name="server-metrics-list"),
    *router.urls,
]
