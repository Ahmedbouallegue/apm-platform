from apps.vendors.views.api import HealthView, VendorViewSet
from apps.vendors.views.web import (
    VendorCreateView,
    VendorDeleteView,
    VendorDetailView,
    VendorListView,
    VendorUpdateView,
)

__all__ = [
    "HealthView",
    "VendorViewSet",
    "VendorListView",
    "VendorDetailView",
    "VendorCreateView",
    "VendorUpdateView",
    "VendorDeleteView",
]
