from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.views import AppHealthView
from apps.notifications.permissions import CanManageNotifications, CanWriteNotifications
from apps.notifications.selectors.notifications import notification_list
from apps.notifications.serializers import NotificationSerializer, NotificationWriteSerializer
from apps.notifications.services.notifications import notification_archive, notification_mark_read


class HealthView(AppHealthView):
    app_name = "notifications"


@extend_schema_view(
    list=extend_schema(tags=["Notifications"]),
    retrieve=extend_schema(tags=["Notifications"]),
    create=extend_schema(tags=["Notifications"]),
    update=extend_schema(tags=["Notifications"]),
    partial_update=extend_schema(tags=["Notifications"]),
    destroy=extend_schema(tags=["Notifications"]),
)
class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageNotifications]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "notification_type", "user"]
    search_fields = ["title", "message"]
    ordering_fields = ["sent_at", "created_at"]
    ordering = ["-sent_at"]

    def get_queryset(self):
        user = self.request.user
        # Viewers/managers see their own; admin/dsi can see all via filter
        if user.is_superuser or user.role in {"admin", "dsi"}:
            return notification_list()
        return notification_list(user=user)

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return NotificationWriteSerializer
        return NotificationSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [CanWriteNotifications()]
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        if notif.user_id != request.user.id and not (
            request.user.is_superuser or request.user.role in {"admin", "dsi"}
        ):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        notification_mark_read(notification=notif)
        return Response(NotificationSerializer(notif).data)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        notif = self.get_object()
        if notif.user_id != request.user.id and not (
            request.user.is_superuser or request.user.role in {"admin", "dsi"}
        ):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        notification_archive(notification=notif)
        return Response(NotificationSerializer(notif).data)
