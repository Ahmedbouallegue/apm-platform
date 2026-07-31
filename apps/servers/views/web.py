from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.servers.forms import ServerForm
from apps.servers.models import Server
from apps.servers.selectors.servers import server_list
from apps.servers.services.servers import server_create, server_soft_delete, server_update


def _can_view(user) -> bool:
    return bool(user.is_authenticated)


def _can_write(user) -> bool:
    return bool(
        user.is_authenticated
        and (user.is_superuser or user.role in {"admin", "dsi", "manager"})
    )


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
@method_decorator(user_passes_test(_can_write), name="dispatch")
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
            server = server_create(data=form.cleaned_data)
            messages.success(request, f"Serveur « {server.name} » créé.")
            return redirect("servers:detail", pk=server.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "title": "Nouveau serveur", "mode": "create"},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write), name="dispatch")
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
            server_update(server=server, data=form.cleaned_data)
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
@method_decorator(user_passes_test(_can_write), name="dispatch")
class ServerDeleteView(View):
    def post(self, request, pk):
        server = get_object_or_404(server_list(), pk=pk)
        label = server.name
        server_soft_delete(server=server)
        messages.warning(request, f"Serveur « {label} » archivé.")
        return redirect("servers:list")
