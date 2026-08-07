from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, mixins, viewsets

from apps.audit.permissions import CanManageAudit
from apps.audit.selectors.audit import audit_log_list
from apps.audit.serializers import AuditLogSerializer
from apps.core.views import AppHealthView


class HealthView(AppHealthView):
    app_name = "audit"


@extend_schema_view(
    list=extend_schema(tags=["Audit"]),
    retrieve=extend_schema(tags=["Audit"]),
)
class AuditLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [CanManageAudit]
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["action", "entity", "user"]
    search_fields = ["action", "entity", "entity_id", "details"]
    ordering_fields = ["occurred_at"]
    ordering = ["-occurred_at"]

    def get_queryset(self):
        return audit_log_list()
