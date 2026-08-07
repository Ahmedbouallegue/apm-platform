from django import forms
from django.core.exceptions import ValidationError

from apps.applications.models import Application
from apps.dependencies.models import Dependency


class DependencyForm(forms.ModelForm):
    class Meta:
        model = Dependency
        fields = (
            "dependency_type",
            "description",
            "source_application",
            "target_application",
            "target_external",
            "is_active",
        )
        widgets = {
            "dependency_type": forms.Select(
                attrs={"class": "field-input", "data-validate": "required"}
            ),
            "description": forms.Textarea(attrs={"class": "field-input", "rows": 3}),
            "source_application": forms.Select(
                attrs={"class": "field-input", "data-validate": "required"}
            ),
            "target_application": forms.Select(attrs={"class": "field-input"}),
            "target_external": forms.TextInput(
                attrs={
                    "class": "field-input",
                    "placeholder": "Active Directory, API tierce…",
                    "data-validate": "max:255",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "field-check"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apps_qs = Application.objects.filter(is_deleted=False).order_by("name")
        self.fields["source_application"].queryset = apps_qs
        self.fields["target_application"].queryset = apps_qs
        self.fields["target_application"].required = False
        self.fields["target_external"].required = False
        self.fields["description"].required = False

    def clean(self):
        cleaned = super().clean()
        source = cleaned.get("source_application")
        target = cleaned.get("target_application")
        external = (cleaned.get("target_external") or "").strip()
        cleaned["target_external"] = external

        if not target and not external:
            raise ValidationError("Indiquez une application cible ou une cible externe.")
        if target and external:
            raise ValidationError("Choisissez soit une application cible, soit une cible externe.")
        if source and target and source.pk == target.pk:
            raise ValidationError("Une application ne peut pas dépendre d'elle-même.")
        return cleaned
