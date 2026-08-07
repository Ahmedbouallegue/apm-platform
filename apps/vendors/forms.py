from django import forms
from django.core.exceptions import ValidationError

from apps.core.validators import require_non_empty, validate_optional_url, validate_phone
from apps.vendors.models import Vendor


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = (
            "name",
            "vendor_type",
            "contact_name",
            "contact_email",
            "contact_phone",
            "website",
            "address",
            "is_active",
            "notes",
        )
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "field-input", "data-validate": "required|min:2|max:255"}
            ),
            "vendor_type": forms.Select(attrs={"class": "field-input", "data-validate": "required"}),
            "contact_name": forms.TextInput(attrs={"class": "field-input", "data-validate": "max:255"}),
            "contact_email": forms.EmailInput(
                attrs={"class": "field-input", "data-validate": "email"}
            ),
            "contact_phone": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "+216 71 000 000", "data-validate": "phone"}
            ),
            "website": forms.URLInput(
                attrs={"class": "field-input", "placeholder": "https://…", "data-validate": "url"}
            ),
            "address": forms.Textarea(attrs={"class": "field-input", "rows": 2}),
            "is_active": forms.CheckboxInput(attrs={"class": "field-check"}),
            "notes": forms.Textarea(attrs={"class": "field-input", "rows": 3}),
        }

    def clean_name(self):
        name = require_non_empty(self.cleaned_data.get("name"), "Le nom")
        qs = Vendor.objects.filter(name__iexact=name, is_deleted=False)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Un fournisseur avec ce nom existe déjà.")
        return name

    def clean_contact_phone(self):
        return validate_phone(self.cleaned_data.get("contact_phone"))

    def clean_website(self):
        return validate_optional_url(self.cleaned_data.get("website"))
