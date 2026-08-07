from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from apps.certificates.permissions import CanManageCertificates, CanWriteCertificates
from apps.certificates.selectors.certificates import certificate_list
from apps.certificates.serializers import CertificateSerializer, CertificateWriteSerializer
from apps.certificates.services.certificates import certificate_soft_delete
from apps.core.views import AppHealthView


class HealthView(AppHealthView):
    app_name = "certificates"


@extend_schema_view(
    list=extend_schema(tags=["Certificats SSL"]),
    retrieve=extend_schema(tags=["Certificats SSL"]),
    create=extend_schema(tags=["Certificats SSL"]),
    update=extend_schema(tags=["Certificats SSL"]),
    partial_update=extend_schema(tags=["Certificats SSL"]),
    destroy=extend_schema(tags=["Certificats SSL"]),
)
class CertificateViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageCertificates]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "status",
        "certificate_type",
        "application",
        "environment",
        "domain",
        "is_active",
    ]
    search_fields = ["common_name", "san_domains", "issuer", "notes"]
    ordering_fields = ["common_name", "expires_at", "created_at"]
    ordering = ["expires_at"]

    def get_queryset(self):
        return certificate_list()

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return CertificateWriteSerializer
        return CertificateSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [CanWriteCertificates()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        certificate_soft_delete(certificate=self.get_object(), user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
