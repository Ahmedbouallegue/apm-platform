from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.applications.models import Application
from apps.certificates.forms import CertificateForm
from apps.certificates.models import Certificate
from apps.certificates.selectors.certificates import certificate_list
from apps.certificates.services.certificates import (
    certificate_create,
    certificate_soft_delete,
    certificate_update,
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
class CertificateListView(ListView):
    template_name = "certificates/list.html"
    context_object_name = "certificates"
    paginate_by = 15

    def get_queryset(self):
        active = self.request.GET.get("active")
        is_active = None
        if active == "1":
            is_active = True
        elif active == "0":
            is_active = False
        app_id = self.request.GET.get("application") or None
        return certificate_list(
            search=self.request.GET.get("q") or None,
            status=self.request.GET.get("status") or None,
            certificate_type=self.request.GET.get("type") or None,
            application_id=int(app_id) if app_id and app_id.isdigit() else None,
            is_active=is_active,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Certificate.Status.choices
        ctx["certificate_types"] = Certificate.CertificateType.choices
        ctx["applications"] = Application.objects.filter(is_deleted=False).order_by("name")
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status"] = self.request.GET.get("status", "")
        ctx["type"] = self.request.GET.get("type", "")
        ctx["application"] = self.request.GET.get("application", "")
        ctx["active"] = self.request.GET.get("active", "")
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class CertificateDetailView(DetailView):
    template_name = "certificates/detail.html"
    context_object_name = "certificate"

    def get_queryset(self):
        return certificate_list(with_related=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write), name="dispatch")
class CertificateCreateView(View):
    template_name = "certificates/form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": CertificateForm(), "title": "Nouveau certificat SSL", "mode": "create"},
        )

    def post(self, request):
        form = CertificateForm(request.POST)
        if form.is_valid():
            cert = certificate_create(data=form.cleaned_data, user=request.user)
            messages.success(request, f"Certificat « {cert.common_name} » créé.")
            return redirect("certificates:detail", pk=cert.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "title": "Nouveau certificat SSL", "mode": "create"},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write), name="dispatch")
class CertificateUpdateView(View):
    template_name = "certificates/form.html"

    def get(self, request, pk):
        cert = get_object_or_404(certificate_list(), pk=pk)
        return render(
            request,
            self.template_name,
            {
                "form": CertificateForm(instance=cert),
                "title": f"Modifier — {cert.common_name}",
                "mode": "edit",
                "certificate": cert,
            },
        )

    def post(self, request, pk):
        cert = get_object_or_404(certificate_list(), pk=pk)
        form = CertificateForm(request.POST, instance=cert)
        if form.is_valid():
            certificate_update(certificate=cert, data=form.cleaned_data, user=request.user)
            messages.success(request, "Certificat mis à jour.")
            return redirect("certificates:detail", pk=cert.pk)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "title": f"Modifier — {cert.common_name}",
                "mode": "edit",
                "certificate": cert,
            },
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write), name="dispatch")
class CertificateDeleteView(View):
    def post(self, request, pk):
        cert = get_object_or_404(certificate_list(), pk=pk)
        label = cert.common_name
        certificate_soft_delete(certificate=cert, user=request.user)
        messages.warning(request, f"Certificat « {label} » archivé.")
        return redirect("certificates:list")
