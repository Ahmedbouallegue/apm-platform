from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.vendors.views.api import HealthView, VendorViewSet

router = DefaultRouter()
router.register("", VendorViewSet, basename="vendor")

urlpatterns = [
    path("health/", HealthView.as_view(), name="vendors-health"),
    *router.urls,
]
