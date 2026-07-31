from django.urls import path

from apps.contracts.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="contracts-health"),
]
