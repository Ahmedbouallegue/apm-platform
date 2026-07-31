from django.urls import path

from apps.technologies.views.web import (
    TechnologyCreateView,
    TechnologyDeleteView,
    TechnologyDetailView,
    TechnologyListView,
    TechnologyUpdateView,
)

app_name = "technologies"

urlpatterns = [
    path("technologies/", TechnologyListView.as_view(), name="list"),
    path("technologies/new/", TechnologyCreateView.as_view(), name="create"),
    path("technologies/<int:pk>/", TechnologyDetailView.as_view(), name="detail"),
    path("technologies/<int:pk>/edit/", TechnologyUpdateView.as_view(), name="edit"),
    path("technologies/<int:pk>/delete/", TechnologyDeleteView.as_view(), name="delete"),
]
