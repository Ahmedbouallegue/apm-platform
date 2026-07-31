from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from apps.core.views import AppHealthView
from apps.servers.permissions import CanManageServers, CanWriteServers
from apps.servers.selectors.servers import server_list
from apps.servers.serializers import ServerSerializer, ServerWriteSerializer
from apps.servers.services.servers import server_soft_delete


class HealthView(AppHealthView):
    app_name = "servers"


@extend_schema_view(
    list=extend_schema(tags=["Serveurs"]),
    retrieve=extend_schema(tags=["Serveurs"]),
    create=extend_schema(tags=["Serveurs"]),
    update=extend_schema(tags=["Serveurs"]),
    partial_update=extend_schema(tags=["Serveurs"]),
    destroy=extend_schema(tags=["Serveurs"]),
)
class ServerViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageServers]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["server_type", "datacenter", "is_active"]
    search_fields = ["name", "ip_address", "os", "datacenter", "notes"]
    ordering_fields = ["name", "ip_address", "server_type", "datacenter", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return server_list()

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return ServerWriteSerializer
        return ServerSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [CanWriteServers()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        server = self.get_object()
        server_soft_delete(server=server)
        return Response(status=status.HTTP_204_NO_CONTENT)
