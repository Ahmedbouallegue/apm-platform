from django.urls import path

from apps.applications.views.web import (
    ApplicationCreateView,
    ApplicationDeleteView,
    ApplicationDetailView,
    ApplicationListView,
    ApplicationUpdateView,
)

app_name = "applications"

urlpatterns = [
    path("applications/", ApplicationListView.as_view(), name="list"),
    path("applications/new/", ApplicationCreateView.as_view(), name="create"),
    path("applications/<int:pk>/", ApplicationDetailView.as_view(), name="detail"),
    path("applications/<int:pk>/edit/", ApplicationUpdateView.as_view(), name="edit"),
    path("applications/<int:pk>/delete/", ApplicationDeleteView.as_view(), name="delete"),
]
