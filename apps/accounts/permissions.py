from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrDSI(BasePermission):
    """Full access for platform administrators and DSI."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.role in {"admin", "dsi"})
        )


class CanManageUsers(BasePermission):
    """
    Admin/DSI: full user management.
    Manager: read-only listing.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.role in {"admin", "dsi"}:
            return True
        if user.role == "manager" and request.method in SAFE_METHODS:
            return True
        return False
