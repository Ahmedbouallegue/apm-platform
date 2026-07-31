from rest_framework.permissions import SAFE_METHODS, BasePermission


class CanManageTechnologies(BasePermission):
    """Admin/DSI/Manager: write. Viewer: read-only."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.role in {"admin", "dsi", "manager"}:
            return True
        if user.role == "viewer" and request.method in SAFE_METHODS:
            return True
        return False


class CanWriteTechnologies(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.role in {"admin", "dsi", "manager"})
        )
