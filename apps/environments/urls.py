from django.urls import path

from apps.environments.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="environments-health"),
]
