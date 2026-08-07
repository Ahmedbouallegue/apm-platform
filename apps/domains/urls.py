from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.domains.views.api import DomainViewSet, HealthView

router = DefaultRouter()
router.register("", DomainViewSet, basename="domain")

urlpatterns = [
    path("health/", HealthView.as_view(), name="domains-health"),
    *router.urls,
]
