from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from datetime import timedelta

from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.accounts.decorators import user_passes_test_or_403
from apps.accounts.roles import can_read, can_write_patrimoine

from apps.servers.forms import ServerForm
from apps.servers.models import Server, ServerMetric
from apps.servers.selectors.servers import server_list
from apps.servers.services.servers import server_create, server_soft_delete, server_update


def _can_view(user) -> bool:
    return can_read(user)


def _can_write(user) -> bool:
    return can_write_patrimoine(user)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class ServerListView(ListView):
    template_name = "servers/list.html"
    context_object_name = "servers"
    paginate_by = 15

    def get_queryset(self):
        active = self.request.GET.get("active")
        is_active = None
        if active == "1":
            is_active = True
        elif active == "0":
            is_active = False
        return server_list(
            search=self.request.GET.get("q") or None,
            server_type=self.request.GET.get("type") or None,
            datacenter=self.request.GET.get("datacenter") or None,
            is_active=is_active,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["server_types"] = Server.ServerType.choices
        ctx["q"] = self.request.GET.get("q", "")
        ctx["type"] = self.request.GET.get("type", "")
        ctx["datacenter"] = self.request.GET.get("datacenter", "")
        ctx["active"] = self.request.GET.get("active", "")
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class ServerDetailView(DetailView):
    template_name = "servers/detail.html"
    context_object_name = "server"

    def get_queryset(self):
        return server_list()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = _can_write(self.request.user)
        ctx["environments"] = self.object.environments.select_related("application").order_by(
            "application__name", "env_type"
        )
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class ServerCreateView(View):
    template_name = "servers/form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": ServerForm(), "title": "Nouveau serveur", "mode": "create"},
        )

    def post(self, request):
        form = ServerForm(request.POST)
        if form.is_valid():
            server = server_create(data=form.cleaned_data, user=request.user)
            messages.success(request, f"Serveur « {server.name} » créé.")
            return redirect("servers:detail", pk=server.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "title": "Nouveau serveur", "mode": "create"},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class ServerUpdateView(View):
    template_name = "servers/form.html"

    def get(self, request, pk):
        server = get_object_or_404(server_list(), pk=pk)
        return render(
            request,
            self.template_name,
            {
                "form": ServerForm(instance=server),
                "title": f"Modifier — {server.name}",
                "mode": "edit",
                "server": server,
            },
        )

    def post(self, request, pk):
        server = get_object_or_404(server_list(), pk=pk)
        form = ServerForm(request.POST, instance=server)
        if form.is_valid():
            server_update(server=server, data=form.cleaned_data, user=request.user)
            messages.success(request, "Serveur mis à jour.")
            return redirect("servers:detail", pk=server.pk)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "title": f"Modifier — {server.name}",
                "mode": "edit",
                "server": server,
            },
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class ServerDeleteView(View):
    def post(self, request, pk):
        server = get_object_or_404(server_list(), pk=pk)
        label = server.name
        server_soft_delete(server=server, user=request.user)
        messages.warning(request, f"Serveur « {label} » archivé.")
        return redirect("servers:list")


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class ServerMonitoringView(DetailView):
    template_name = "servers/monitoring.html"
    context_object_name = "server"

    def get_queryset(self):
        return server_list()

    def get(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return self._json_metrics(request)
        return super().get(request, *args, **kwargs)

    def _json_metrics(self, request):
        server = self.get_object()
        hours = int(request.GET.get("hours", 24))
        since = timezone.now() - timedelta(hours=hours)
        qs = ServerMetric.objects.filter(
            server=server, collected_at__gte=since
        ).order_by("collected_at")
        data = list(
            qs.values(
                "cpu_percent",
                "memory_percent",
                "disk_percent",
                "load_avg_1",
                "net_bytes_sent",
                "net_bytes_recv",
                "collected_at",
            )
        )
        for d in data:
            d["collected_at"] = d["collected_at"].isoformat()
        latest = qs.order_by("-collected_at").first()
        summary = {}
        if latest:
            summary = {
                "cpu": latest.cpu_percent,
                "ram": latest.memory_percent,
                "disk": latest.disk_percent,
                "uptime_h": round(latest.uptime_seconds / 3600, 1),
                "load": latest.load_avg_1,
                "collected_at": latest.collected_at.isoformat(),
            }
        return JsonResponse({"metrics": data, "summary": summary})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = _can_write(self.request.user)
        latest = ServerMetric.objects.filter(server=self.object).order_by("-collected_at").first()
        ctx["latest_metric"] = latest
        return ctx
