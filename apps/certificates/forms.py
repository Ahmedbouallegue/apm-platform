from django import forms
from django.core.exceptions import ValidationError

from apps.applications.models import Application
from apps.certificates.models import Certificate
from apps.core.validators import require_non_empty, validate_date_range
from apps.domains.models import Domain
from apps.environments.models import Environment


class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = (
            "common_name",
            "san_domains",
            "issuer",
            "certificate_type",
            "status",
            "application",
            "environment",
            "domain",
            "issued_at",
            "expires_at",
            "auto_renew",
            "is_active",
            "notes",
        )
        widgets = {
            "common_name": forms.TextInput(
                attrs={
                    "class": "field-input",
                    "placeholder": "*.topnet.tn",
                    "data-validate": "required|min:3|max:255",
                }
            ),
            "san_domains": forms.Textarea(
                attrs={
                    "class": "field-input",
                    "rows": 2,
                    "placeholder": "www.topnet.tn, api.topnet.tn",
                }
            ),
            "issuer": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "Let's Encrypt, DigiCert…"}
            ),
            "certificate_type": forms.Select(attrs={"class": "field-input", "data-validate": "required"}),
            "status": forms.Select(attrs={"class": "field-input", "data-validate": "required"}),
            "application": forms.Select(attrs={"class": "field-input"}),
            "environment": forms.Select(attrs={"class": "field-input"}),
            "domain": forms.Select(attrs={"class": "field-input"}),
            "issued_at": forms.DateInput(attrs={"class": "field-input", "type": "date"}),
            "expires_at": forms.DateInput(
                attrs={"class": "field-input", "type": "date", "data-validate": "required"}
            ),
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
        self.fields["domain"].queryset = Domain.objects.filter(is_deleted=False)
        self.fields["domain"].required = False
        self.fields["issued_at"].required = False

    def clean_common_name(self):
        return require_non_empty(self.cleaned_data.get("common_name"), "Le nom commun").lower()

    def clean_expires_at(self):
        value = self.cleaned_data.get("expires_at")
        if not value:
            raise ValidationError("La date d'expiration est obligatoire.")
        return value

    def clean(self):
        cleaned = super().clean()
        validate_date_range(
            cleaned.get("issued_at"),
            cleaned.get("expires_at"),
            start_label="Date d'émission",
            end_label="Date d'expiration",
        )
        return cleaned
