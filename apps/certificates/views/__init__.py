from apps.certificates.views.api import CertificateViewSet, HealthView
from apps.certificates.views.web import (
    CertificateCreateView,
    CertificateDeleteView,
    CertificateDetailView,
    CertificateListView,
    CertificateUpdateView,
)

__all__ = [
    "HealthView",
    "CertificateViewSet",
    "CertificateListView",
    "CertificateDetailView",
    "CertificateCreateView",
    "CertificateUpdateView",
    "CertificateDeleteView",
]
