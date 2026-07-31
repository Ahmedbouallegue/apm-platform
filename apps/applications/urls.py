from django.urls import path

from apps.applications.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="applications-health"),
]
