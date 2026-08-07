from django import forms
from django.core.exceptions import ValidationError

from apps.applications.models import Application
from apps.core.validators import require_non_empty, validate_date_range
from apps.domains.models import Domain
from apps.environments.models import Environment


class DomainForm(forms.ModelForm):
    class Meta:
        model = Domain
        fields = (
            "fqdn",
            "registrar",
            "dns_provider",
            "registered_at",
            "expires_at",
            "status",
            "application",
            "environment",
            "is_primary",
            "auto_renew",
            "is_active",
            "notes",
        )
        widgets = {
            "fqdn": forms.TextInput(
                attrs={
                    "class": "field-input",
                    "placeholder": "app.topnet.tn",
                    "data-validate": "required|min:3|max:255",
                }
            ),
            "registrar": forms.TextInput(attrs={"class": "field-input", "data-validate": "max:255"}),
            "dns_provider": forms.TextInput(attrs={"class": "field-input", "data-validate": "max:255"}),
            "registered_at": forms.DateInput(attrs={"class": "field-input", "type": "date"}),
            "expires_at": forms.DateInput(attrs={"class": "field-input", "type": "date"}),
            "status": forms.Select(attrs={"class": "field-input", "data-validate": "required"}),
            "application": forms.Select(attrs={"class": "field-input"}),
            "environment": forms.Select(attrs={"class": "field-input"}),
            "is_primary": forms.CheckboxInput(attrs={"class": "field-check"}),
            "auto_renew": forms.CheckboxInput(attrs={"class": "field-check"}),
            "is_active": forms.CheckboxInput(attrs={"class": "field-check"}),
            "notes": forms.Textarea(attrs={"class": "field-input", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["application"].queryset = Application.objects.filter(is_deleted=False)
        self.fields["application"].required = False
        self.fields["environment"].queryset = Environment.objects.select_related("application")
        self.fields["environment"].required = False
        self.fields["registered_at"].required = False
        self.fields["expires_at"].required = False

    def clean_fqdn(self):
        fqdn = require_non_empty(self.cleaned_data.get("fqdn"), "Le nom de domaine").lower()
        qs = Domain.objects.filter(fqdn__iexact=fqdn, is_deleted=False)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Ce nom de domaine existe déjà.")
        return fqdn

    def clean(self):
        cleaned = super().clean()
        validate_date_range(
            cleaned.get("registered_at"),
            cleaned.get("expires_at"),
            start_label="Date d'enregistrement",
            end_label="Date d'expiration",
        )
        return cleaned
