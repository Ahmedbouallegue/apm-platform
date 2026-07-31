from django import forms

from apps.applications.models import Application
from apps.core.validators import require_non_empty, validate_optional_url, validate_resource_label
from apps.environments.models import Environment


class EnvironmentForm(forms.ModelForm):
    class Meta:
        model = Environment
        fields = (
            "application",
            "server",
            "name",
            "env_type",
            "url",
            "ip_address",
            "os",
            "cpu",
            "ram",
            "hosting_provider",
            "docker",
            "kubernetes",
            "is_active",
        )
        widgets = {
            "application": forms.Select(
                attrs={"class": "field-input", "data-validate": "required"}
            ),
            "server": forms.Select(attrs={"class": "field-input"}),
            "name": forms.TextInput(
                attrs={"class": "field-input", "data-validate": "required|min:2|max:255"}
            ),
            "env_type": forms.Select(
                attrs={"class": "field-input", "data-validate": "required"}
            ),
            "url": forms.TextInput(
                attrs={
                    "class": "field-input",
                    "placeholder": "https://...",
                    "data-validate": "url|max:200",
                }
            ),
            "ip_address": forms.TextInput(
                attrs={
                    "class": "field-input",
                    "placeholder": "10.0.0.1",
                    "data-validate": "ip",
                }
            ),
            "os": forms.TextInput(attrs={"class": "field-input", "placeholder": "Linux / Windows"}),
            "cpu": forms.TextInput(attrs={"class": "field-input", "placeholder": "4 vCPU"}),
            "ram": forms.TextInput(attrs={"class": "field-input", "placeholder": "8 Go"}),
            "hosting_provider": forms.TextInput(
                attrs={"class": "field-input", "data-validate": "max:255"}
            ),
            "docker": forms.CheckboxInput(attrs={"class": "field-check"}),
            "kubernetes": forms.CheckboxInput(attrs={"class": "field-check"}),
            "is_active": forms.CheckboxInput(attrs={"class": "field-check"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.servers.models import Server

        self.fields["application"].queryset = Application.objects.filter(is_deleted=False).order_by(
            "name"
        )
        self.fields["server"].queryset = Server.objects.filter(
            is_deleted=False, is_active=True
        ).order_by("name")
        self.fields["server"].required = False
        self.fields["application"].required = True
        self.fields["env_type"].required = True
        self.fields["name"].required = True
        self.fields["ip_address"].required = False

    def clean_name(self):
        return require_non_empty(self.cleaned_data.get("name"), "Le nom")

    def clean_url(self):
        return validate_optional_url(self.cleaned_data.get("url"))

    def clean_cpu(self):
        return validate_resource_label(self.cleaned_data.get("cpu"), "CPU")

    def clean_ram(self):
        return validate_resource_label(self.cleaned_data.get("ram"), "RAM")

    def clean(self):
        cleaned = super().clean()
        application = cleaned.get("application")
        env_type = cleaned.get("env_type")
        if application and env_type:
            qs = Environment.objects.filter(application=application, env_type=env_type)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error(
                    "env_type",
                    "Cet environnement (DEV/RECETTE/PREPROD/PROD) existe déjà pour cette application.",
                )
        server = cleaned.get("server")
        if server and server.is_deleted:
            self.add_error("server", "Ce serveur est archivé et ne peut pas être sélectionné.")
        return cleaned
