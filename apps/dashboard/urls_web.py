from django.urls import path

from apps.dashboard.views.web import DashboardHomeView

app_name = "dashboard"

urlpatterns = [
    path("dashboard/", DashboardHomeView.as_view(), name="home"),
]
