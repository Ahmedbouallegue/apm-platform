from django import forms
from django.core.exceptions import ValidationError

from apps.core.validators import validate_tech_name, validate_version
from apps.technologies.models import Technology


class TechnologyForm(forms.ModelForm):
    class Meta:
        model = Technology
        fields = ("name", "tech_type", "version", "description")
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "field-input",
                    "placeholder": "Ex. PostgreSQL",
                    "data-validate": "required|min:2|max:128",
                }
            ),
            "tech_type": forms.Select(
                attrs={"class": "field-input", "data-validate": "required"}
            ),
            "version": forms.TextInput(
                attrs={
                    "class": "field-input",
                    "placeholder": "Ex. 16",
                    "data-validate": "version|max:64",
                }
            ),
            "description": forms.Textarea(
                attrs={"class": "field-input", "rows": 4, "data-validate": "max:5000"}
            ),
        }

    def clean_name(self):
        return validate_tech_name(self.cleaned_data.get("name"))

    def clean_version(self):
        return validate_version(self.cleaned_data.get("version"))

    def clean(self):
        cleaned = super().clean()
        name = cleaned.get("name")
        version = cleaned.get("version") or ""
        if name:
            qs = Technology.objects.filter(name__iexact=name, version=version)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    "Cette technologie (nom + version) existe déjà dans le référentiel."
                )
        return cleaned
