from django.urls import path

from apps.servers.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="servers-health"),
]
