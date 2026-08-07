from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.views import AppHealthView
from apps.dashboard.selectors.dashboard import dashboard_stats


class HealthView(AppHealthView):
    app_name = "dashboard"


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Dashboard"])
    def get(self, request):
        return Response(dashboard_stats(user=request.user))
