from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.applications.permissions import CanManageApplications, CanWriteApplications
from apps.applications.selectors.applications import application_list
from apps.applications.serializers import ApplicationSerializer, ApplicationWriteSerializer
from apps.applications.services.applications import application_restore, application_soft_delete
from apps.core.views import AppHealthView


class HealthView(AppHealthView):
    app_name = "applications"


@extend_schema_view(
    list=extend_schema(tags=["Applications"]),
    retrieve=extend_schema(tags=["Applications"]),
    create=extend_schema(tags=["Applications"]),
    update=extend_schema(tags=["Applications"]),
    partial_update=extend_schema(tags=["Applications"]),
    destroy=extend_schema(tags=["Applications"]),
)
class ApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageApplications]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "criticality", "business_unit", "owner"]
    search_fields = ["name", "description", "business_unit"]
    ordering_fields = ["name", "status", "criticality", "go_live_date", "user_count", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        include_deleted = self.request.query_params.get("include_deleted") == "1"
        if self.action in {"restore"}:
            include_deleted = True
        return application_list(include_deleted=include_deleted)

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return ApplicationWriteSerializer
        return ApplicationSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy", "restore"}:
            return [CanWriteApplications()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        application = self.get_object()
        application_soft_delete(application=application, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], permission_classes=[CanWriteApplications])
    def restore(self, request, pk=None):
        application = self.get_queryset().get(pk=pk)
        application_restore(application=application, user=request.user)
        return Response(ApplicationSerializer(application).data)
