from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.applications.models import Application
from apps.environments.forms import EnvironmentForm
from apps.environments.models import Environment
from apps.environments.selectors.environments import environment_list
from apps.environments.services.environments import (
    environment_create,
    environment_delete,
    environment_update,
)


def _can_view(user) -> bool:
    return bool(user.is_authenticated)


def _can_write(user) -> bool:
    return bool(
        user.is_authenticated
        and (user.is_superuser or user.role in {"admin", "dsi", "manager"})
    )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class EnvironmentListView(ListView):
    template_name = "environments/list.html"
    context_object_name = "environments"
    paginate_by = 15

    def get_queryset(self):
        active = self.request.GET.get("active")
        is_active = None
        if active == "1":
            is_active = True
        elif active == "0":
            is_active = False
        app_id = self.request.GET.get("application")
        return environment_list(
            search=self.request.GET.get("q") or None,
            env_type=self.request.GET.get("type") or None,
            application_id=int(app_id) if app_id and app_id.isdigit() else None,
            is_active=is_active,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["env_types"] = Environment.EnvType.choices
        ctx["applications"] = Application.objects.filter(is_deleted=False).order_by("name")
        ctx["q"] = self.request.GET.get("q", "")
        ctx["type"] = self.request.GET.get("type", "")
        ctx["application"] = self.request.GET.get("application", "")
        ctx["active"] = self.request.GET.get("active", "")
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class EnvironmentDetailView(DetailView):
    template_name = "environments/detail.html"
    context_object_name = "environment"

    def get_queryset(self):
        return environment_list()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write), name="dispatch")
class EnvironmentCreateView(View):
    template_name = "environments/form.html"

    def get(self, request):
        initial = {}
        app_id = request.GET.get("application")
        if app_id and app_id.isdigit():
            initial["application"] = app_id
        env_type = request.GET.get("type")
        if env_type in dict(Environment.EnvType.choices):
            initial["env_type"] = env_type
            initial["name"] = dict(Environment.EnvType.choices)[env_type]
        return render(
            request,
            self.template_name,
            {
                "form": EnvironmentForm(initial=initial),
                "title": "Nouvel environnement",
                "mode": "create",
            },
        )

    def post(self, request):
        form = EnvironmentForm(request.POST)
        if form.is_valid():
            env = environment_create(data=form.cleaned_data, user=request.user)
            messages.success(request, f"Environnement « {env} » créé.")
            return redirect("environments:detail", pk=env.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "title": "Nouvel environnement", "mode": "create"},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write), name="dispatch")
class EnvironmentUpdateView(View):
    template_name = "environments/form.html"

    def get(self, request, pk):
        env = get_object_or_404(environment_list(), pk=pk)
        return render(
            request,
            self.template_name,
            {
                "form": EnvironmentForm(instance=env),
                "title": f"Modifier — {env}",
                "mode": "edit",
                "environment": env,
            },
        )

    def post(self, request, pk):
        env = get_object_or_404(environment_list(), pk=pk)
        form = EnvironmentForm(request.POST, instance=env)
        if form.is_valid():
            environment_update(environment=env, data=form.cleaned_data, user=request.user)
            messages.success(request, "Environnement mis à jour.")
            return redirect("environments:detail", pk=env.pk)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "title": f"Modifier — {env}",
                "mode": "edit",
                "environment": env,
            },
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write), name="dispatch")
class EnvironmentDeleteView(View):
    def post(self, request, pk):
        env = get_object_or_404(environment_list(), pk=pk)
        label = str(env)
        environment_delete(environment=env, user=request.user)
        messages.warning(request, f"Environnement « {label} » supprimé.")
        return redirect("environments:list")
