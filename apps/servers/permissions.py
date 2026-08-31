from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.roles import can_read_infrastructure, can_write_infrastructure


class CanManageServers(BasePermission):
    """DSI/Manager/System: write. Viewer: read-only."""

    def has_permission(self, request, view) -> bool:
        if not can_read_infrastructure(request.user):
            return False
        if request.method in SAFE_METHODS:
            return True
        return can_write_infrastructure(request.user)


class CanWriteServers(BasePermission):
    def has_permission(self, request, view) -> bool:
        return can_write_infrastructure(request.user)
