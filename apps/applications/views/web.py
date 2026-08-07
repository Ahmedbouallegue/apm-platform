from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.applications.forms import ApplicationForm
from apps.applications.models import Application
from apps.applications.selectors.applications import application_list
from apps.applications.services.applications import (
    application_create,
    application_soft_delete,
    application_update,
)


def _can_view_apps(user) -> bool:
    return bool(user.is_authenticated)


def _can_write_apps(user) -> bool:
    return bool(
        user.is_authenticated
        and (user.is_superuser or user.role in {"admin", "dsi", "manager"})
    )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view_apps), name="dispatch")
class ApplicationListView(ListView):
    template_name = "applications/list.html"
    context_object_name = "applications"
    paginate_by = 12

    def get_queryset(self):
        return application_list(
            search=self.request.GET.get("q") or None,
            status=self.request.GET.get("status") or None,
            criticality=self.request.GET.get("criticality") or None,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Application.Status.choices
        ctx["criticalities"] = Application.Criticality.choices
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status"] = self.request.GET.get("status", "")
        ctx["criticality"] = self.request.GET.get("criticality", "")
        ctx["can_write"] = _can_write_apps(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view_apps), name="dispatch")
class ApplicationDetailView(DetailView):
    template_name = "applications/detail.html"
    context_object_name = "application"

    def get_queryset(self):
        return application_list().prefetch_related("technologies")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = _can_write_apps(self.request.user)
        ctx["environments"] = (
            self.object.environments.select_related("server").order_by("env_type")
        )
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write_apps), name="dispatch")
class ApplicationCreateView(View):
    template_name = "applications/form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": ApplicationForm(), "title": "Nouvelle application", "mode": "create"},
        )

    def post(self, request):
        form = ApplicationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            technologies = data.pop("technologies")
            application_create(
                data=data,
                technology_ids=list(technologies.values_list("pk", flat=True)),
                user=request.user,
            )
            messages.success(request, "Application créée avec succès.")
            return redirect("applications:list")
        return render(
            request,
            self.template_name,
            {"form": form, "title": "Nouvelle application", "mode": "create"},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write_apps), name="dispatch")
class ApplicationUpdateView(View):
    template_name = "applications/form.html"

    def get(self, request, pk):
        app = get_object_or_404(application_list(), pk=pk)
        form = ApplicationForm(instance=app)
        return render(
            request,
            self.template_name,
            {"form": form, "title": f"Modifier — {app.name}", "mode": "edit", "application": app},
        )

    def post(self, request, pk):
        app = get_object_or_404(application_list(), pk=pk)
        form = ApplicationForm(request.POST, instance=app)
        if form.is_valid():
            data = form.cleaned_data
            technologies = data.pop("technologies")
            application_update(
                application=app,
                data=data,
                technology_ids=list(technologies.values_list("pk", flat=True)),
                user=request.user,
            )
            messages.success(request, "Application mise à jour.")
            return redirect("applications:detail", pk=app.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "title": f"Modifier — {app.name}", "mode": "edit", "application": app},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write_apps), name="dispatch")
class ApplicationDeleteView(View):
    def post(self, request, pk):
        app = get_object_or_404(application_list(), pk=pk)
        application_soft_delete(application=app, user=request.user)
        messages.warning(request, f"Application « {app.name} » archivée.")
        return redirect("applications:list")
