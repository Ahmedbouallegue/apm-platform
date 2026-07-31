from django.urls import path

from apps.documents.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="documents-health"),
]
