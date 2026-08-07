from django.urls import path

from apps.incidents.views.web import (
    IncidentCreateView,
    IncidentDeleteView,
    IncidentDetailView,
    IncidentListView,
    IncidentUpdateView,
)

app_name = "incidents"

urlpatterns = [
    path("incidents/", IncidentListView.as_view(), name="list"),
    path("incidents/new/", IncidentCreateView.as_view(), name="create"),
    path("incidents/<int:pk>/", IncidentDetailView.as_view(), name="detail"),
    path("incidents/<int:pk>/edit/", IncidentUpdateView.as_view(), name="edit"),
    path("incidents/<int:pk>/delete/", IncidentDeleteView.as_view(), name="delete"),
]
