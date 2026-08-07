from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from apps.core.views import AppHealthView
from apps.domains.permissions import CanManageDomains, CanWriteDomains
from apps.domains.selectors.domains import domain_list
from apps.domains.serializers import DomainSerializer, DomainWriteSerializer
from apps.domains.services.domains import domain_soft_delete


class HealthView(AppHealthView):
    app_name = "domains"


@extend_schema_view(
    list=extend_schema(tags=["Domaines"]),
    retrieve=extend_schema(tags=["Domaines"]),
    create=extend_schema(tags=["Domaines"]),
    update=extend_schema(tags=["Domaines"]),
    partial_update=extend_schema(tags=["Domaines"]),
    destroy=extend_schema(tags=["Domaines"]),
)
class DomainViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageDomains]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "application", "environment", "is_primary", "is_active"]
    search_fields = ["fqdn", "registrar", "dns_provider", "notes"]
    ordering_fields = ["fqdn", "expires_at", "created_at"]
    ordering = ["fqdn"]

    def get_queryset(self):
        return domain_list()

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return DomainWriteSerializer
        return DomainSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [CanWriteDomains()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        domain_soft_delete(domain=self.get_object(), user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
