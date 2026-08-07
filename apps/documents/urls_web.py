from django.urls import path

from apps.documents.views.web import (
    DocumentCreateView,
    DocumentDeleteView,
    DocumentDetailView,
    DocumentListView,
    DocumentUpdateView,
)

app_name = "documents"

urlpatterns = [
    path("documents/", DocumentListView.as_view(), name="list"),
    path("documents/new/", DocumentCreateView.as_view(), name="create"),
    path("documents/<int:pk>/", DocumentDetailView.as_view(), name="detail"),
    path("documents/<int:pk>/edit/", DocumentUpdateView.as_view(), name="edit"),
    path("documents/<int:pk>/delete/", DocumentDeleteView.as_view(), name="delete"),
]
