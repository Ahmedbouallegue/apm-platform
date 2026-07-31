from django.urls import path

from apps.audit.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="audit-health"),
]
