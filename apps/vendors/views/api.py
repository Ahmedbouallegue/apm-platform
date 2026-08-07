from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from apps.core.views import AppHealthView
from apps.vendors.permissions import CanManageVendors, CanWriteVendors
from apps.vendors.selectors.vendors import vendor_list
from apps.vendors.serializers import VendorSerializer, VendorWriteSerializer
from apps.vendors.services.vendors import vendor_soft_delete


class HealthView(AppHealthView):
    app_name = "vendors"


@extend_schema_view(
    list=extend_schema(tags=["Fournisseurs"]),
    retrieve=extend_schema(tags=["Fournisseurs"]),
    create=extend_schema(tags=["Fournisseurs"]),
    update=extend_schema(tags=["Fournisseurs"]),
    partial_update=extend_schema(tags=["Fournisseurs"]),
    destroy=extend_schema(tags=["Fournisseurs"]),
)
class VendorViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageVendors]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["vendor_type", "is_active"]
    search_fields = ["name", "contact_name", "contact_email", "notes"]
    ordering_fields = ["name", "vendor_type", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return vendor_list()

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return VendorWriteSerializer
        return VendorSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [CanWriteVendors()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        vendor_soft_delete(vendor=self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)
