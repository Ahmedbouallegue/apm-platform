from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets

from apps.core.views import AppHealthView
from apps.technologies.permissions import CanManageTechnologies, CanWriteTechnologies
from apps.technologies.selectors.technologies import technology_list
from apps.technologies.serializers import TechnologySerializer, TechnologyWriteSerializer


class HealthView(AppHealthView):
    app_name = "technologies"


@extend_schema_view(
    list=extend_schema(tags=["Technologies"]),
    retrieve=extend_schema(tags=["Technologies"]),
    create=extend_schema(tags=["Technologies"]),
    update=extend_schema(tags=["Technologies"]),
    partial_update=extend_schema(tags=["Technologies"]),
    destroy=extend_schema(tags=["Technologies"]),
)
class TechnologyViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageTechnologies]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["tech_type"]
    search_fields = ["name", "version", "description"]
    ordering_fields = ["name", "tech_type", "version", "created_at"]
    ordering = ["name", "version"]

    def get_queryset(self):
        return technology_list()

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return TechnologyWriteSerializer
        return TechnologySerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [CanWriteTechnologies()]
        return super().get_permissions()
