from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.notifications.views.api import HealthView, NotificationViewSet

router = DefaultRouter()
router.register("", NotificationViewSet, basename="notification")

urlpatterns = [
    path("health/", HealthView.as_view(), name="notifications-health"),
    *router.urls,
]
