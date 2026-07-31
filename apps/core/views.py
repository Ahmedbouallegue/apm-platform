from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.serializers import AppHealthSerializer


class AppHealthView(APIView):
    """Shared stub health endpoint used by domain apps during early sprints."""

    authentication_classes = []
    permission_classes = []
    serializer_class = AppHealthSerializer
    app_name = "core"

    @extend_schema(
        tags=["Health"],
        responses={200: AppHealthSerializer},
        description="Stub endpoint confirming the application module is wired.",
    )
    def get(self, request):
        payload = {"app": self.app_name, "status": "ready"}
        return Response(AppHealthSerializer(payload).data)
