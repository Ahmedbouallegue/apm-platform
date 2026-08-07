from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from apps.dashboard.selectors.dashboard import dashboard_stats


@method_decorator(login_required, name="dispatch")
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
