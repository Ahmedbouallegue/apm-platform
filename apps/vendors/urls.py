from django.urls import path

from apps.vendors.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="vendors-health"),
]
