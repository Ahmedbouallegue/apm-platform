from django.urls import path

from apps.contracts.views.web import (
    ContractCreateView,
    ContractDeleteView,
    ContractDetailView,
    ContractListView,
    ContractUpdateView,
)

app_name = "contracts"

urlpatterns = [
    path("contracts/", ContractListView.as_view(), name="list"),
    path("contracts/new/", ContractCreateView.as_view(), name="create"),
    path("contracts/<int:pk>/", ContractDetailView.as_view(), name="detail"),
    path("contracts/<int:pk>/edit/", ContractUpdateView.as_view(), name="edit"),
    path("contracts/<int:pk>/delete/", ContractDeleteView.as_view(), name="delete"),
]
