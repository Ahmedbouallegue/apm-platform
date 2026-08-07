from django import forms

from apps.applications.models import Application
from apps.core.validators import require_non_empty
from apps.incidents.models import Incident


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = (
            "title",
            "description",
            "occurred_at",
            "impact",
            "root_cause",
            "solution",
            "status",
            "application",
        )
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "field-input", "data-validate": "required|min:3|max:255"}
            ),
            "description": forms.Textarea(
                attrs={"class": "field-input", "rows": 4, "data-validate": "required"}
            ),
            "occurred_at": forms.DateTimeInput(
                attrs={"class": "field-input", "type": "datetime-local", "data-validate": "required"}
            ),
            "impact": forms.Select(attrs={"class": "field-input", "data-validate": "required"}),
            "root_cause": forms.Textarea(attrs={"class": "field-input", "rows": 3}),
            "solution": forms.Textarea(attrs={"class": "field-input", "rows": 3}),
            "status": forms.Select(attrs={"class": "field-input", "data-validate": "required"}),
            "application": forms.Select(attrs={"class": "field-input", "data-validate": "required"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["application"].queryset = Application.objects.filter(is_deleted=False).order_by(
            "name"
        )
        self.fields["root_cause"].required = False
        self.fields["solution"].required = False
        if self.instance and self.instance.pk and self.instance.occurred_at:
            self.initial["occurred_at"] = self.instance.occurred_at.strftime("%Y-%m-%dT%H:%M")

    def clean_title(self):
        return require_non_empty(self.cleaned_data.get("title"), "Le titre")

    def clean_description(self):
        return require_non_empty(self.cleaned_data.get("description"), "La description")
