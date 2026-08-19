from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.accounts.decorators import user_passes_test_or_403
from apps.accounts.roles import can_read, can_write_patrimoine

from apps.technologies.forms import TechnologyForm
from apps.technologies.models import Technology
from apps.technologies.selectors.technologies import technology_list
from apps.technologies.services.technologies import (
    technology_create,
    technology_delete,
    technology_update,
)


def _can_view(user) -> bool:
    return can_read(user)


def _can_write(user) -> bool:
    return can_write_patrimoine(user)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class TechnologyListView(ListView):
    template_name = "technologies/list.html"
    context_object_name = "technologies"
    paginate_by = 15

    def get_queryset(self):
        return technology_list(
            search=self.request.GET.get("q") or None,
            tech_type=self.request.GET.get("type") or None,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["types"] = Technology.TechType.choices
        ctx["q"] = self.request.GET.get("q", "")
        ctx["type"] = self.request.GET.get("type", "")
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class TechnologyDetailView(DetailView):
    template_name = "technologies/detail.html"
    context_object_name = "technology"

    def get_queryset(self):
        return technology_list()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = _can_write(self.request.user)
        ctx["linked_apps"] = self.object.applications.filter(is_deleted=False).order_by("name")
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class TechnologyCreateView(View):
    template_name = "technologies/form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": TechnologyForm(), "title": "Nouvelle technologie", "mode": "create"},
        )

    def post(self, request):
        form = TechnologyForm(request.POST)
        if form.is_valid():
            tech = technology_create(data=form.cleaned_data)
            messages.success(request, f"Technologie « {tech} » créée.")
            return redirect("technologies:detail", pk=tech.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "title": "Nouvelle technologie", "mode": "create"},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class TechnologyUpdateView(View):
    template_name = "technologies/form.html"

    def get(self, request, pk):
        tech = get_object_or_404(technology_list(), pk=pk)
        return render(
            request,
            self.template_name,
            {
                "form": TechnologyForm(instance=tech),
                "title": f"Modifier — {tech}",
                "mode": "edit",
                "technology": tech,
            },
        )

    def post(self, request, pk):
        tech = get_object_or_404(technology_list(), pk=pk)
        form = TechnologyForm(request.POST, instance=tech)
        if form.is_valid():
            technology_update(technology=tech, data=form.cleaned_data)
            messages.success(request, "Technologie mise à jour.")
            return redirect("technologies:detail", pk=tech.pk)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "title": f"Modifier — {tech}",
                "mode": "edit",
                "technology": tech,
            },
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class TechnologyDeleteView(View):
    def post(self, request, pk):
        tech = get_object_or_404(technology_list(), pk=pk)
        label = str(tech)
        technology_delete(technology=tech)
        messages.warning(request, f"Technologie « {label} » supprimée.")
        return redirect("technologies:list")
