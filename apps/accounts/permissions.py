from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.roles import can_manage_users, can_write_users, is_admin_dsi


class IsAdminOrDSI(BasePermission):
    """Full access for platform administrators and DSI."""

    def has_permission(self, request, view) -> bool:
        return is_admin_dsi(request.user)


class CanManageUsers(BasePermission):
    """
    Admin/DSI: full user management.
    Manager (Équipe DSI): read-only listing.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not can_manage_users(user):
            return False
        if can_write_users(user):
            return True
        return request.method in SAFE_METHODS
