from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets

from apps.core.views import AppHealthView
from apps.environments.permissions import CanManageEnvironments, CanWriteEnvironments
from apps.environments.selectors.environments import environment_list
from apps.environments.serializers import EnvironmentSerializer, EnvironmentWriteSerializer


class HealthView(AppHealthView):
    app_name = "environments"


@extend_schema_view(
    list=extend_schema(tags=["Environnements"]),
    retrieve=extend_schema(tags=["Environnements"]),
    create=extend_schema(tags=["Environnements"]),
    update=extend_schema(tags=["Environnements"]),
    partial_update=extend_schema(tags=["Environnements"]),
    destroy=extend_schema(tags=["Environnements"]),
)
class EnvironmentViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageEnvironments]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["env_type", "application", "is_active", "docker", "kubernetes"]
    search_fields = ["name", "url", "ip_address", "application__name", "hosting_provider", "os"]
    ordering_fields = ["name", "env_type", "application__name", "created_at"]
    ordering = ["application__name", "env_type"]

    def get_queryset(self):
        return environment_list()

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return EnvironmentWriteSerializer
        return EnvironmentSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [CanWriteEnvironments()]
        return super().get_permissions()
