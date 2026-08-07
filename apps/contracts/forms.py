from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.applications.models import Application
from apps.contracts.models import Contract
from apps.core.validators import require_non_empty, validate_date_range
from apps.vendors.models import Vendor

User = get_user_model()


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = (
            "reference",
            "title",
            "vendor",
            "application",
            "contract_type",
            "status",
            "start_date",
            "end_date",
            "annual_cost",
            "currency",
            "auto_renew",
            "sla_level",
            "owner",
            "is_active",
            "notes",
        )
        widgets = {
            "reference": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "CTR-2026-001", "data-validate": "required|max:64"}
            ),
            "title": forms.TextInput(attrs={"class": "field-input", "data-validate": "required|min:3|max:255"}),
            "vendor": forms.Select(attrs={"class": "field-input", "data-validate": "required"}),
            "application": forms.Select(attrs={"class": "field-input"}),
            "contract_type": forms.Select(attrs={"class": "field-input", "data-validate": "required"}),
            "status": forms.Select(attrs={"class": "field-input", "data-validate": "required"}),
            "start_date": forms.DateInput(attrs={"class": "field-input", "type": "date", "data-validate": "required"}),
            "end_date": forms.DateInput(attrs={"class": "field-input", "type": "date", "data-validate": "required"}),
            "annual_cost": forms.NumberInput(attrs={"class": "field-input", "step": "0.001"}),
            "currency": forms.TextInput(attrs={"class": "field-input", "data-validate": "max:3"}),
            "auto_renew": forms.CheckboxInput(attrs={"class": "field-check"}),
            "sla_level": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "24/7, J+1…", "data-validate": "max:64"}
            ),
            "owner": forms.Select(attrs={"class": "field-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "field-check"}),
            "notes": forms.Textarea(attrs={"class": "field-input", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vendor"].queryset = Vendor.objects.filter(is_deleted=False, is_active=True)
        self.fields["application"].queryset = Application.objects.filter(is_deleted=False)
        self.fields["application"].required = False
        self.fields["owner"].queryset = User.objects.filter(is_active=True).order_by("username")
        self.fields["owner"].required = False
        self.fields["annual_cost"].required = False

    def clean_reference(self):
        ref = require_non_empty(self.cleaned_data.get("reference"), "La référence")
        qs = Contract.objects.filter(reference__iexact=ref, is_deleted=False)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Cette référence de contrat existe déjà.")
        return ref

    def clean_title(self):
        return require_non_empty(self.cleaned_data.get("title"), "L'intitulé")

    def clean(self):
        cleaned = super().clean()
        validate_date_range(cleaned.get("start_date"), cleaned.get("end_date"))
        return cleaned
