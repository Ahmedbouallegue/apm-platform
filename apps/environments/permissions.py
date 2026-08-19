from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.roles import can_read, can_write_patrimoine


class CanManageEnvironments(BasePermission):
    """Admin/DSI/Manager: full access. Viewer: read-only (even if is_superuser)."""

    def has_permission(self, request, view) -> bool:
        if not can_read(request.user):
            return False
        if request.method in SAFE_METHODS:
            return True
        return can_write_patrimoine(request.user)


class CanWriteEnvironments(BasePermission):
    def has_permission(self, request, view) -> bool:
        return can_write_patrimoine(request.user)
