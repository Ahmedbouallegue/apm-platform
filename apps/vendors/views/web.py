from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.vendors.forms import VendorForm
from apps.vendors.models import Vendor
from apps.vendors.selectors.vendors import vendor_list
from apps.vendors.services.vendors import vendor_create, vendor_soft_delete, vendor_update


def _can_view(user) -> bool:
    return bool(user.is_authenticated)


def _can_write(user) -> bool:
    return bool(
        user.is_authenticated
        and (user.is_superuser or user.role in {"admin", "dsi", "manager"})
    )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class VendorListView(ListView):
    template_name = "vendors/list.html"
    context_object_name = "vendors"
    paginate_by = 15

    def get_queryset(self):
        active = self.request.GET.get("active")
        is_active = None
        if active == "1":
            is_active = True
        elif active == "0":
            is_active = False
        return vendor_list(
            search=self.request.GET.get("q") or None,
            vendor_type=self.request.GET.get("type") or None,
            is_active=is_active,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["vendor_types"] = Vendor.VendorType.choices
        ctx["q"] = self.request.GET.get("q", "")
        ctx["type"] = self.request.GET.get("type", "")
        ctx["active"] = self.request.GET.get("active", "")
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class VendorDetailView(DetailView):
    template_name = "vendors/detail.html"
    context_object_name = "vendor"

    def get_queryset(self):
        return vendor_list()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = _can_write(self.request.user)
        ctx["contracts"] = self.object.contracts.filter(is_deleted=False).select_related(
            "application"
        )
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write), name="dispatch")
class VendorCreateView(View):
    template_name = "vendors/form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": VendorForm(), "title": "Nouveau fournisseur", "mode": "create"},
        )

    def post(self, request):
        form = VendorForm(request.POST)
        if form.is_valid():
            vendor = vendor_create(data=form.cleaned_data)
            messages.success(request, f"Fournisseur « {vendor.name} » créé.")
            return redirect("vendors:detail", pk=vendor.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "title": "Nouveau fournisseur", "mode": "create"},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write), name="dispatch")
class VendorUpdateView(View):
    template_name = "vendors/form.html"

    def get(self, request, pk):
        vendor = get_object_or_404(vendor_list(), pk=pk)
        return render(
            request,
            self.template_name,
            {
                "form": VendorForm(instance=vendor),
                "title": f"Modifier — {vendor.name}",
                "mode": "edit",
                "vendor": vendor,
            },
        )

    def post(self, request, pk):
        vendor = get_object_or_404(vendor_list(), pk=pk)
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            vendor_update(vendor=vendor, data=form.cleaned_data)
            messages.success(request, "Fournisseur mis à jour.")
            return redirect("vendors:detail", pk=vendor.pk)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "title": f"Modifier — {vendor.name}",
                "mode": "edit",
                "vendor": vendor,
            },
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write), name="dispatch")
class VendorDeleteView(View):
    def post(self, request, pk):
        vendor = get_object_or_404(vendor_list(), pk=pk)
        label = vendor.name
        vendor_soft_delete(vendor=vendor)
        messages.warning(request, f"Fournisseur « {label} » archivé.")
        return redirect("vendors:list")
