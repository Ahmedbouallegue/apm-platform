from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.servers.views.api import HealthView, ServerViewSet

router = DefaultRouter()
router.register("", ServerViewSet, basename="server")

urlpatterns = [
    path("health/", HealthView.as_view(), name="servers-health"),
    *router.urls,
]
