from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from apps.core.views import AppHealthView
from apps.incidents.permissions import CanManageIncidents, CanWriteIncidents
from apps.incidents.selectors.incidents import incident_list
from apps.incidents.serializers import IncidentSerializer, IncidentWriteSerializer
from apps.incidents.services.incidents import incident_soft_delete


class HealthView(AppHealthView):
    app_name = "incidents"


@extend_schema_view(
    list=extend_schema(tags=["Incidents"]),
    retrieve=extend_schema(tags=["Incidents"]),
    create=extend_schema(tags=["Incidents"]),
    update=extend_schema(tags=["Incidents"]),
    partial_update=extend_schema(tags=["Incidents"]),
    destroy=extend_schema(tags=["Incidents"]),
)
class IncidentViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageIncidents]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "impact", "application"]
    search_fields = ["title", "description", "root_cause", "solution"]
    ordering_fields = ["occurred_at", "title", "created_at"]
    ordering = ["-occurred_at"]

    def get_queryset(self):
        return incident_list()

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return IncidentWriteSerializer
        return IncidentSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [CanWriteIncidents()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        incident_soft_delete(incident=self.get_object(), user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
