from django.urls import path

from apps.dashboard.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="dashboard-health"),
]
