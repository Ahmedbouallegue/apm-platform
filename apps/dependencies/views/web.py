from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.accounts.decorators import user_passes_test_or_403
from apps.accounts.roles import can_read, can_write_patrimoine

from apps.applications.models import Application
from apps.dependencies.forms import DependencyForm
from apps.dependencies.models import Dependency
from apps.dependencies.selectors.dependencies import dependency_list
from apps.dependencies.services.dependencies import (
    dependency_create,
    dependency_soft_delete,
    dependency_update,
)


def _can_view(user) -> bool:
    return can_read(user)


def _can_write(user) -> bool:
    return can_write_patrimoine(user)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class DependencyListView(ListView):
    template_name = "dependencies/list.html"
    context_object_name = "dependencies"
    paginate_by = 15

    def get_queryset(self):
        active = self.request.GET.get("active")
        is_active = None
        if active == "1":
            is_active = True
        elif active == "0":
            is_active = False
        source_id = self.request.GET.get("source") or None
        target_id = self.request.GET.get("target") or None
        return dependency_list(
            search=self.request.GET.get("q") or None,
            dependency_type=self.request.GET.get("type") or None,
            source_id=int(source_id) if source_id and source_id.isdigit() else None,
            target_id=int(target_id) if target_id and target_id.isdigit() else None,
            is_active=is_active,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["dependency_types"] = Dependency.DependencyType.choices
        ctx["applications"] = Application.objects.filter(is_deleted=False).order_by("name")
        ctx["q"] = self.request.GET.get("q", "")
        ctx["type"] = self.request.GET.get("type", "")
        ctx["source"] = self.request.GET.get("source", "")
        ctx["target"] = self.request.GET.get("target", "")
        ctx["active"] = self.request.GET.get("active", "")
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class DependencyDetailView(DetailView):
    template_name = "dependencies/detail.html"
    context_object_name = "dependency"

    def get_queryset(self):
        return dependency_list()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class DependencyCreateView(View):
    template_name = "dependencies/form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": DependencyForm(), "title": "Nouvelle dépendance", "mode": "create"},
        )

    def post(self, request):
        form = DependencyForm(request.POST)
        if form.is_valid():
            dependency = dependency_create(data=form.cleaned_data, user=request.user)
            messages.success(request, f"Dépendance « {dependency} » créée.")
            return redirect("dependencies:detail", pk=dependency.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "title": "Nouvelle dépendance", "mode": "create"},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class DependencyUpdateView(View):
    template_name = "dependencies/form.html"

    def get(self, request, pk):
        dependency = get_object_or_404(dependency_list(), pk=pk)
        return render(
            request,
            self.template_name,
            {
                "form": DependencyForm(instance=dependency),
                "title": f"Modifier — {dependency}",
                "mode": "edit",
                "dependency": dependency,
            },
        )

    def post(self, request, pk):
        dependency = get_object_or_404(dependency_list(), pk=pk)
        form = DependencyForm(request.POST, instance=dependency)
        if form.is_valid():
            dependency_update(dependency=dependency, data=form.cleaned_data, user=request.user)
            messages.success(request, "Dépendance mise à jour.")
            return redirect("dependencies:detail", pk=dependency.pk)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "title": f"Modifier — {dependency}",
                "mode": "edit",
                "dependency": dependency,
            },
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class DependencyDeleteView(View):
    def post(self, request, pk):
        dependency = get_object_or_404(dependency_list(), pk=pk)
        label = str(dependency)
        dependency_soft_delete(dependency=dependency, user=request.user)
        messages.warning(request, f"Dépendance « {label} » archivée.")
        return redirect("dependencies:list")
