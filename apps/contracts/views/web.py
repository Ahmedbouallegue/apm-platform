from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.accounts.decorators import user_passes_test_or_403
from apps.accounts.roles import can_read, can_write_patrimoine

from apps.contracts.forms import ContractForm
from apps.contracts.models import Contract
from apps.contracts.selectors.contracts import contract_list
from apps.contracts.services.contracts import contract_create, contract_soft_delete, contract_update
from apps.vendors.models import Vendor


def _can_view(user) -> bool:
    return can_read(user)


def _can_write(user) -> bool:
    return can_write_patrimoine(user)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class ContractListView(ListView):
    template_name = "contracts/list.html"
    context_object_name = "contracts"
    paginate_by = 15

    def get_queryset(self):
        active = self.request.GET.get("active")
        is_active = None
        if active == "1":
            is_active = True
        elif active == "0":
            is_active = False
        vendor_id = self.request.GET.get("vendor") or None
        return contract_list(
            search=self.request.GET.get("q") or None,
            contract_type=self.request.GET.get("type") or None,
            status=self.request.GET.get("status") or None,
            vendor_id=int(vendor_id) if vendor_id and vendor_id.isdigit() else None,
            is_active=is_active,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["contract_types"] = Contract.ContractType.choices
        ctx["statuses"] = Contract.Status.choices
        ctx["vendors"] = Vendor.objects.filter(is_deleted=False).order_by("name")
        ctx["q"] = self.request.GET.get("q", "")
        ctx["type"] = self.request.GET.get("type", "")
        ctx["status"] = self.request.GET.get("status", "")
        ctx["vendor"] = self.request.GET.get("vendor", "")
        ctx["active"] = self.request.GET.get("active", "")
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class ContractDetailView(DetailView):
    template_name = "contracts/detail.html"
    context_object_name = "contract"

    def get_queryset(self):
        return contract_list()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class ContractCreateView(View):
    template_name = "contracts/form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": ContractForm(), "title": "Nouveau contrat", "mode": "create"},
        )

    def post(self, request):
        form = ContractForm(request.POST)
        if form.is_valid():
            contract = contract_create(data=form.cleaned_data, user=request.user)
            messages.success(request, f"Contrat « {contract.reference} » créé.")
            return redirect("contracts:detail", pk=contract.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "title": "Nouveau contrat", "mode": "create"},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class ContractUpdateView(View):
    template_name = "contracts/form.html"

    def get(self, request, pk):
        contract = get_object_or_404(contract_list(), pk=pk)
        return render(
            request,
            self.template_name,
            {
                "form": ContractForm(instance=contract),
                "title": f"Modifier — {contract.reference}",
                "mode": "edit",
                "contract": contract,
            },
        )

    def post(self, request, pk):
        contract = get_object_or_404(contract_list(), pk=pk)
        form = ContractForm(request.POST, instance=contract)
        if form.is_valid():
            contract_update(contract=contract, data=form.cleaned_data, user=request.user)
            messages.success(request, "Contrat mis à jour.")
            return redirect("contracts:detail", pk=contract.pk)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "title": f"Modifier — {contract.reference}",
                "mode": "edit",
                "contract": contract,
            },
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(_can_write), name="dispatch")
class ContractDeleteView(View):
    def post(self, request, pk):
        contract = get_object_or_404(contract_list(), pk=pk)
        label = contract.reference
        contract_soft_delete(contract=contract, user=request.user)
        messages.warning(request, f"Contrat « {label} » archivé.")
        return redirect("contracts:list")
