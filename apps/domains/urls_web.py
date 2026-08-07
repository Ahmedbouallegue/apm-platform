from django.urls import path

from apps.domains.views.web import (
    DomainCreateView,
    DomainDeleteView,
    DomainDetailView,
    DomainListView,
    DomainUpdateView,
)

app_name = "domains"

urlpatterns = [
    path("domains/", DomainListView.as_view(), name="list"),
    path("domains/new/", DomainCreateView.as_view(), name="create"),
    path("domains/<int:pk>/", DomainDetailView.as_view(), name="detail"),
    path("domains/<int:pk>/edit/", DomainUpdateView.as_view(), name="edit"),
    path("domains/<int:pk>/delete/", DomainDeleteView.as_view(), name="delete"),
]
