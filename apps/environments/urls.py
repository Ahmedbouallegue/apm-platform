from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.environments.views.api import EnvironmentViewSet, HealthView

router = DefaultRouter()
router.register("", EnvironmentViewSet, basename="environment")

urlpatterns = [
    path("health/", HealthView.as_view(), name="environments-health"),
    *router.urls,
]
