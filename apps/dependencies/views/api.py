from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from apps.core.views import AppHealthView
from apps.dependencies.permissions import CanManageDependencies, CanWriteDependencies
from apps.dependencies.selectors.dependencies import dependency_list
from apps.dependencies.serializers import DependencySerializer, DependencyWriteSerializer
from apps.dependencies.services.dependencies import dependency_soft_delete


class HealthView(AppHealthView):
    app_name = "dependencies"


@extend_schema_view(
    list=extend_schema(tags=["Dépendances"]),
    retrieve=extend_schema(tags=["Dépendances"]),
    create=extend_schema(tags=["Dépendances"]),
    update=extend_schema(tags=["Dépendances"]),
    partial_update=extend_schema(tags=["Dépendances"]),
    destroy=extend_schema(tags=["Dépendances"]),
)
class DependencyViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageDependencies]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["dependency_type", "source_application", "target_application", "is_active"]
    search_fields = ["description", "target_external", "source_application__name"]
    ordering_fields = ["created_at", "dependency_type"]
    ordering = ["source_application__name"]

    def get_queryset(self):
        return dependency_list()

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return DependencyWriteSerializer
        return DependencySerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [CanWriteDependencies()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        dependency_soft_delete(dependency=self.get_object(), user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
