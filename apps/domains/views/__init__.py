from apps.domains.views.api import DomainViewSet, HealthView
from apps.domains.views.web import (
    DomainCreateView,
    DomainDeleteView,
    DomainDetailView,
    DomainListView,
    DomainUpdateView,
)

__all__ = [
    "HealthView",
    "DomainViewSet",
    "DomainListView",
    "DomainDetailView",
    "DomainCreateView",
    "DomainUpdateView",
    "DomainDeleteView",
]
