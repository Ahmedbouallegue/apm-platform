from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.technologies.views.api import HealthView, TechnologyViewSet

router = DefaultRouter()
router.register("", TechnologyViewSet, basename="technology")

urlpatterns = [
    path("health/", HealthView.as_view(), name="technologies-health"),
    *router.urls,
]
