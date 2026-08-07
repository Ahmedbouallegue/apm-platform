from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from apps.contracts.permissions import CanManageContracts, CanWriteContracts
from apps.contracts.selectors.contracts import contract_list
from apps.contracts.serializers import ContractSerializer, ContractWriteSerializer
from apps.contracts.services.contracts import contract_soft_delete
from apps.core.views import AppHealthView


class HealthView(AppHealthView):
    app_name = "contracts"


@extend_schema_view(
    list=extend_schema(tags=["Contrats"]),
    retrieve=extend_schema(tags=["Contrats"]),
    create=extend_schema(tags=["Contrats"]),
    update=extend_schema(tags=["Contrats"]),
    partial_update=extend_schema(tags=["Contrats"]),
    destroy=extend_schema(tags=["Contrats"]),
)
class ContractViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageContracts]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["contract_type", "status", "vendor", "application", "is_active"]
    search_fields = ["reference", "title", "sla_level", "notes", "vendor__name"]
    ordering_fields = ["reference", "end_date", "start_date", "created_at"]
    ordering = ["-end_date"]

    def get_queryset(self):
        return contract_list()

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return ContractWriteSerializer
        return ContractSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [CanWriteContracts()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        contract_soft_delete(contract=self.get_object(), user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
