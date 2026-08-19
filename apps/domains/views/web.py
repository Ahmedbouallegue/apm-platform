from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.accounts.decorators import user_passes_test_or_403
from apps.accounts.roles import can_read, can_write_patrimoine

from apps.applications.models import Application
from apps.domains.forms import DomainForm
from apps.domains.models import Domain
from apps.domains.selectors.domains import domain_list
from apps.domains.services.domains import domain_create, domain_soft_delete, domain_update


def _can_view(user) -> bool:
    return can_read(user)


def _can_write(user) -> bool:
    return can_write_patrimoine(user)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class DomainListView(ListView):
    template_name = "domains/list.html"
    context_object_name = "domains"
    paginate_by = 15

    def get_queryset(self):
        active = self.request.GET.get("active")
        is_active = None
        if active == "1":
            is_active = True
        elif active == "0":
            is_active = False
        app_id = self.request.GET.get("application") or None
        return domain_list(
            search=self.request.GET.get("q") or None,
            status=self.request.GET.get("status") or None,
            application_id=int(app_id) if app_id and app_id.isdigit() else None,
            is_active=is_active,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Domain.Status.choices
        ctx["applications"] = Application.objects.filter(is_deleted=False).order_by("name")
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status"] = self.request.GET.get("status", "")
        ctx["application"] = self.request.GET.get("application", "")
        ctx["active"] = self.request.GET.get("active", "")
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class DomainDetailView(DetailView):
    template_name = "domains/detail.html"
    context_object_name = "domain"

    def get_queryset(self):
        return domain_list()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = _can_write(self.request.user)
        ctx["certificates"] = self.object.certificates.filter(is_deleted=False)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class DomainCreateView(View):
    template_name = "domains/form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": DomainForm(), "title": "Nouveau domaine", "mode": "create"},
        )

    def post(self, request):
        form = DomainForm(request.POST)
        if form.is_valid():
            domain = domain_create(data=form.cleaned_data, user=request.user)
            messages.success(request, f"Domaine « {domain.fqdn} » créé.")
            return redirect("domains:detail", pk=domain.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "title": "Nouveau domaine", "mode": "create"},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class DomainUpdateView(View):
    template_name = "domains/form.html"

    def get(self, request, pk):
        domain = get_object_or_404(domain_list(), pk=pk)
        return render(
            request,
            self.template_name,
            {
                "form": DomainForm(instance=domain),
                "title": f"Modifier — {domain.fqdn}",
                "mode": "edit",
                "domain": domain,
            },
        )

    def post(self, request, pk):
        domain = get_object_or_404(domain_list(), pk=pk)
        form = DomainForm(request.POST, instance=domain)
        if form.is_valid():
            domain_update(domain=domain, data=form.cleaned_data, user=request.user)
            messages.success(request, "Domaine mis à jour.")
            return redirect("domains:detail", pk=domain.pk)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "title": f"Modifier — {domain.fqdn}",
                "mode": "edit",
                "domain": domain,
            },
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class DomainDeleteView(View):
    def post(self, request, pk):
        domain = get_object_or_404(domain_list(), pk=pk)
        label = domain.fqdn
        domain_soft_delete(domain=domain, user=request.user)
        messages.warning(request, f"Domaine « {label} » archivé.")
        return redirect("domains:list")
