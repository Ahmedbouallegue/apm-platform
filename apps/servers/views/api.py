from datetime import timedelta

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.views import AppHealthView
from apps.servers.models import ServerMetric
from apps.servers.permissions import CanManageServers, CanWriteServers
from apps.servers.selectors.servers import server_list
from apps.servers.serializers import ServerSerializer, ServerWriteSerializer
from apps.servers.serializers.metrics import (
    ServerMetricReadSerializer,
    ServerMetricWriteSerializer,
)
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
        server_soft_delete(server=server, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServerMetricIngestView(APIView):
    """POST endpoint for VM agents to push performance metrics."""

    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Métriques VM"], request=ServerMetricWriteSerializer)
    def post(self, request):
        serializer = ServerMetricWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        metric = serializer.save()
        return Response(
            {"id": metric.id, "server": metric.server_id},
            status=status.HTTP_201_CREATED,
        )


class ServerMetricListView(APIView):
    """GET endpoint to read metrics for a specific server."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Métriques VM"],
        parameters=[
            OpenApiParameter("server_id", int, required=True),
            OpenApiParameter("hours", int, required=False, description="Heures d'historique (défaut 24)"),
        ],
    )
    def get(self, request):
        server_id = request.query_params.get("server_id")
        if not server_id:
            return Response(
                {"detail": "server_id requis."}, status=status.HTTP_400_BAD_REQUEST
            )
        hours = int(request.query_params.get("hours", 24))
        since = timezone.now() - timedelta(hours=hours)
        qs = (
            ServerMetric.objects.filter(server_id=server_id, collected_at__gte=since)
            .select_related("server")
            .order_by("collected_at")
        )
        serializer = ServerMetricReadSerializer(qs, many=True)
        return Response(serializer.data)
