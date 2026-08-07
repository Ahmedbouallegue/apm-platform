from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.dependencies.views.api import DependencyViewSet, HealthView

router = DefaultRouter()
router.register("", DependencyViewSet, basename="dependency")

urlpatterns = [
    path("health/", HealthView.as_view(), name="dependencies-health"),
    *router.urls,
]
