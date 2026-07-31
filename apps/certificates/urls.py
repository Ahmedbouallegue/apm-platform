from django.urls import path

from apps.certificates.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="certificates-health"),
]
