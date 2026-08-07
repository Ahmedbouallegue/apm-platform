from django.urls import path

from apps.certificates.views.web import (
    CertificateCreateView,
    CertificateDeleteView,
    CertificateDetailView,
    CertificateListView,
    CertificateUpdateView,
)

app_name = "certificates"

urlpatterns = [
    path("certificates/", CertificateListView.as_view(), name="list"),
    path("certificates/new/", CertificateCreateView.as_view(), name="create"),
    path("certificates/<int:pk>/", CertificateDetailView.as_view(), name="detail"),
    path("certificates/<int:pk>/edit/", CertificateUpdateView.as_view(), name="edit"),
    path("certificates/<int:pk>/delete/", CertificateDeleteView.as_view(), name="delete"),
]
