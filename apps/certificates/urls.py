from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.certificates.views.api import CertificateViewSet, HealthView

router = DefaultRouter()
router.register("", CertificateViewSet, basename="certificate")

urlpatterns = [
    path("health/", HealthView.as_view(), name="certificates-health"),
    *router.urls,
]
