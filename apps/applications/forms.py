from django import forms
from django.core.exceptions import ValidationError

from apps.applications.models import Application
from apps.core.validators import validate_app_name, validate_date_range
from apps.technologies.models import Technology


class ApplicationForm(forms.ModelForm):
    technologies = forms.ModelMultipleChoiceField(
        queryset=Technology.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "field-input", "size": "6"}),
        label="Technologies",
    )

    class Meta:
        model = Application
        fields = (
            "name",
            "description",
            "criticality",
            "status",
            "go_live_date",
            "end_of_life_date",
            "user_count",
            "business_unit",
            "owner",
            "technologies",
        )
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "field-input", "data-validate": "required|min:2|max:255"}
            ),
            "description": forms.Textarea(
                attrs={"class": "field-input", "rows": 4, "data-validate": "max:5000"}
            ),
            "criticality": forms.Select(
                attrs={"class": "field-input", "data-validate": "required"}
            ),
            "status": forms.Select(attrs={"class": "field-input", "data-validate": "required"}),
            "go_live_date": forms.DateInput(attrs={"class": "field-input", "type": "date"}),
            "end_of_life_date": forms.DateInput(
                attrs={
                    "class": "field-input",
                    "type": "date",
                    "data-validate": "dateAfter:go_live_date",
                }
            ),
            "user_count": forms.NumberInput(
                attrs={"class": "field-input", "data-validate": "numberMin:0"}
            ),
            "business_unit": forms.TextInput(
                attrs={"class": "field-input", "data-validate": "max:255"}
            ),
            "owner": forms.Select(attrs={"class": "field-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["owner"].queryset = self.fields["owner"].queryset.order_by("username")
        self.fields["owner"].required = False
        self.fields["name"].required = True
        self.fields["criticality"].required = True
        self.fields["status"].required = True

    def clean_name(self):
        name = validate_app_name(self.cleaned_data.get("name"))
        qs = Application.objects.filter(name__iexact=name, is_deleted=False)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Une application avec ce nom existe déjà.")
        return name

    def clean_user_count(self):
        value = self.cleaned_data.get("user_count")
        if value is None:
            return 0
        if value < 0:
            raise ValidationError("Le nombre d'utilisateurs ne peut pas être négatif.")
        if value > 10_000_000:
            raise ValidationError("Nombre d'utilisateurs trop élevé.")
        return value

    def clean(self):
        cleaned = super().clean()
        try:
            validate_date_range(
                cleaned.get("go_live_date"),
                cleaned.get("end_of_life_date"),
                start_label="Date de mise en production",
                end_label="Date de fin de vie",
            )
        except ValidationError as exc:
            self.add_error("end_of_life_date", exc)
        return cleaned
