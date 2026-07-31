from rest_framework.permissions import SAFE_METHODS, BasePermission


class CanUseAssistant(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.role in {"admin", "dsi", "manager", "viewer"}:
            return True
        return False


class CanManageKnowledge(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.role in {"admin", "dsi", "manager"}:
            return True
        if user.role == "viewer" and request.method in SAFE_METHODS:
            return True
        return False
