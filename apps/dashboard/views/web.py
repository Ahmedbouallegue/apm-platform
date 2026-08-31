from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from apps.accounts.decorators import user_passes_test_or_403
from apps.accounts.roles import can_read_infrastructure, can_read_patrimoine
from apps.dashboard.selectors.dashboard import dashboard_stats


def _can_view_dashboard(user) -> bool:
    return can_read_patrimoine(user) or can_read_infrastructure(user)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_view_dashboard), name="dispatch")
class DashboardHomeView(View):
    template_name = "dashboard/home.html"

    def get(self, request):
        stats = dashboard_stats(user=request.user)
        return render(
            request,
            self.template_name,
            {
                "stats": stats,
                "charts_json": stats.get("charts") or {},
            },
        )
