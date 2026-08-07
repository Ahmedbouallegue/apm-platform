from apps.contracts.views.api import ContractViewSet, HealthView
from apps.contracts.views.web import (
    ContractCreateView,
    ContractDeleteView,
    ContractDetailView,
    ContractListView,
    ContractUpdateView,
)

__all__ = [
    "HealthView",
    "ContractViewSet",
    "ContractListView",
    "ContractDetailView",
    "ContractCreateView",
    "ContractUpdateView",
    "ContractDeleteView",
]
