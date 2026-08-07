from django.urls import path

from apps.vendors.views.web import (
    VendorCreateView,
    VendorDeleteView,
    VendorDetailView,
    VendorListView,
    VendorUpdateView,
)

app_name = "vendors"

urlpatterns = [
    path("vendors/", VendorListView.as_view(), name="list"),
    path("vendors/new/", VendorCreateView.as_view(), name="create"),
    path("vendors/<int:pk>/", VendorDetailView.as_view(), name="detail"),
    path("vendors/<int:pk>/edit/", VendorUpdateView.as_view(), name="edit"),
    path("vendors/<int:pk>/delete/", VendorDeleteView.as_view(), name="delete"),
]
