from django.urls import path

from apps.incidents.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="incidents-health"),
]
