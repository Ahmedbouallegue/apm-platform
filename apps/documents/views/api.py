from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from apps.core.views import AppHealthView
from apps.documents.permissions import CanManageDocuments, CanWriteDocuments
from apps.documents.selectors.documents import document_list, tag_list
from apps.documents.serializers import DocumentSerializer, DocumentWriteSerializer, TagSerializer
from apps.documents.services.documents import document_soft_delete


class HealthView(AppHealthView):
    app_name = "documents"


@extend_schema_view(
    list=extend_schema(tags=["Documents"]),
    retrieve=extend_schema(tags=["Documents"]),
    create=extend_schema(tags=["Documents"]),
    update=extend_schema(tags=["Documents"]),
    partial_update=extend_schema(tags=["Documents"]),
    destroy=extend_schema(tags=["Documents"]),
)
class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageDocuments]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "application", "is_active"]
    search_fields = ["title", "description", "file_type"]
    ordering_fields = ["title", "uploaded_at", "created_at"]
    ordering = ["-uploaded_at"]

    def get_queryset(self):
        return document_list()

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return DocumentWriteSerializer
        return DocumentSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [CanWriteDocuments()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        document_soft_delete(document=self.get_object(), user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(tags=["Tags"]),
    retrieve=extend_schema(tags=["Tags"]),
    create=extend_schema(tags=["Tags"]),
    destroy=extend_schema(tags=["Tags"]),
)
class TagViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageDocuments]
    http_method_names = ["get", "post", "delete", "head", "options"]
    serializer_class = TagSerializer
    search_fields = ["name"]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ["name"]

    def get_queryset(self):
        return tag_list()

    def get_permissions(self):
        if self.action in {"create", "destroy"}:
            return [CanWriteDocuments()]
        return super().get_permissions()
