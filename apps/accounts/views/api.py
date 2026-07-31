from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import CanManageUsers, IsAdminOrDSI
from apps.accounts.selectors.users import user_list
from apps.accounts.serializers import (
    MeSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from apps.accounts.services.users import user_activate, user_deactivate

User = get_user_model()


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MeSerializer

    @extend_schema(tags=["Accounts"], responses={200: MeSerializer})
    def get(self, request):
        return Response(MeSerializer(request.user).data)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageUsers]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["role", "is_active", "department"]
    search_fields = ["username", "email", "first_name", "last_name", "department"]
    ordering_fields = ["username", "email", "role", "date_joined", "last_login"]
    ordering = ["username"]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return user_list()

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in {"update", "partial_update"}:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy", "deactivate", "activate"}:
            return [IsAdminOrDSI()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        """Soft-deactivate instead of hard delete."""
        user = self.get_object()
        if user.pk == request.user.pk:
            return Response(
                {"detail": "Vous ne pouvez pas désactiver votre propre compte."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_deactivate(user=user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrDSI])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        if user.pk == request.user.pk:
            return Response(
                {"detail": "Vous ne pouvez pas désactiver votre propre compte."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_deactivate(user=user)
        return Response(UserSerializer(user).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrDSI])
    def activate(self, request, pk=None):
        user = self.get_object()
        user_activate(user=user)
        return Response(UserSerializer(user).data)
