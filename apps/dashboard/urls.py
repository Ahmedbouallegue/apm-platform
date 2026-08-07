from django.urls import path

from apps.dashboard.views.api import DashboardStatsView, HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="dashboard-health"),
    path("stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
]
