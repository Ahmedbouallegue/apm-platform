from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.applications.views.api import ApplicationViewSet, HealthView

router = DefaultRouter()
router.register("", ApplicationViewSet, basename="application")

urlpatterns = [
    path("health/", HealthView.as_view(), name="applications-health"),
    *router.urls,
]
