from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.incidents.views.api import HealthView, IncidentViewSet

router = DefaultRouter()
router.register("", IncidentViewSet, basename="incident")

urlpatterns = [
    path("health/", HealthView.as_view(), name="incidents-health"),
    *router.urls,
]
