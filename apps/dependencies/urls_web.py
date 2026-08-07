from django.urls import path

from apps.dependencies.views.web import (
    DependencyCreateView,
    DependencyDeleteView,
    DependencyDetailView,
    DependencyListView,
    DependencyUpdateView,
)

app_name = "dependencies"

urlpatterns = [
    path("dependencies/", DependencyListView.as_view(), name="list"),
    path("dependencies/new/", DependencyCreateView.as_view(), name="create"),
    path("dependencies/<int:pk>/", DependencyDetailView.as_view(), name="detail"),
    path("dependencies/<int:pk>/edit/", DependencyUpdateView.as_view(), name="edit"),
    path("dependencies/<int:pk>/delete/", DependencyDeleteView.as_view(), name="delete"),
]
