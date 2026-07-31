from django.urls import path

from apps.environments.views.web import (
    EnvironmentCreateView,
    EnvironmentDeleteView,
    EnvironmentDetailView,
    EnvironmentListView,
    EnvironmentUpdateView,
)

app_name = "environments"

urlpatterns = [
    path("environments/", EnvironmentListView.as_view(), name="list"),
    path("environments/new/", EnvironmentCreateView.as_view(), name="create"),
    path("environments/<int:pk>/", EnvironmentDetailView.as_view(), name="detail"),
    path("environments/<int:pk>/edit/", EnvironmentUpdateView.as_view(), name="edit"),
    path("environments/<int:pk>/delete/", EnvironmentDeleteView.as_view(), name="delete"),
]
