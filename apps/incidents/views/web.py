from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.accounts.decorators import user_passes_test_or_403
from apps.accounts.roles import can_read, can_write_patrimoine

from apps.applications.models import Application
from apps.incidents.forms import IncidentForm
from apps.incidents.models import Incident
from apps.incidents.selectors.incidents import incident_list
from apps.incidents.services.incidents import (
    incident_create,
    incident_soft_delete,
    incident_update,
)


def _can_view(user) -> bool:
    return can_read(user)


def _can_write(user) -> bool:
    return can_write_patrimoine(user)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class IncidentListView(ListView):
    template_name = "incidents/list.html"
    context_object_name = "incidents"
    paginate_by = 15

    def get_queryset(self):
        application_id = self.request.GET.get("application") or None
        return incident_list(
            search=self.request.GET.get("q") or None,
            status=self.request.GET.get("status") or None,
            impact=self.request.GET.get("impact") or None,
            application_id=int(application_id) if application_id and application_id.isdigit() else None,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Incident.Status.choices
        ctx["impacts"] = Incident.Impact.choices
        ctx["applications"] = Application.objects.filter(is_deleted=False).order_by("name")
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status"] = self.request.GET.get("status", "")
        ctx["impact"] = self.request.GET.get("impact", "")
        ctx["application"] = self.request.GET.get("application", "")
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class IncidentDetailView(DetailView):
    template_name = "incidents/detail.html"
    context_object_name = "incident"

    def get_queryset(self):
        return incident_list()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class IncidentCreateView(View):
    template_name = "incidents/form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": IncidentForm(), "title": "Nouvel incident", "mode": "create"},
        )

    def post(self, request):
        form = IncidentForm(request.POST)
        if form.is_valid():
            incident = incident_create(data=form.cleaned_data, user=request.user)
            messages.success(request, f"Incident « {incident.title} » créé.")
            return redirect("incidents:detail", pk=incident.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "title": "Nouvel incident", "mode": "create"},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class IncidentUpdateView(View):
    template_name = "incidents/form.html"

    def get(self, request, pk):
        incident = get_object_or_404(incident_list(), pk=pk)
        return render(
            request,
            self.template_name,
            {
                "form": IncidentForm(instance=incident),
                "title": f"Modifier — {incident.title}",
                "mode": "edit",
                "incident": incident,
            },
        )

    def post(self, request, pk):
        incident = get_object_or_404(incident_list(), pk=pk)
        form = IncidentForm(request.POST, instance=incident)
        if form.is_valid():
            incident_update(incident=incident, data=form.cleaned_data, user=request.user)
            messages.success(request, "Incident mis à jour.")
            return redirect("incidents:detail", pk=incident.pk)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "title": f"Modifier — {incident.title}",
                "mode": "edit",
                "incident": incident,
            },
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class IncidentDeleteView(View):
    def post(self, request, pk):
        incident = get_object_or_404(incident_list(), pk=pk)
        label = incident.title
        incident_soft_delete(incident=incident, user=request.user)
        messages.warning(request, f"Incident « {label} » archivé.")
        return redirect("incidents:list")
