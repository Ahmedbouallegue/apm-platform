from django import forms
from django.core.exceptions import ValidationError

from apps.core.validators import (
    require_non_empty,
    validate_resource_label,
    validate_server_name,
)
from apps.servers.models import Server


class ServerForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = (
            "name",
            "ip_address",
            "os",
            "cpu",
            "ram",
            "datacenter",
            "server_type",
            "is_active",
            "notes",
        )
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "field-input",
                    "placeholder": "srv-app-01",
                    "data-validate": "required|serverName|max:255",
                }
            ),
            "ip_address": forms.TextInput(
                attrs={
                    "class": "field-input",
                    "placeholder": "10.0.0.10",
                    "data-validate": "required|ip",
                }
            ),
            "os": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "Ubuntu 22.04", "data-validate": "max:128"}
            ),
            "cpu": forms.TextInput(attrs={"class": "field-input", "placeholder": "8 vCPU"}),
            "ram": forms.TextInput(attrs={"class": "field-input", "placeholder": "32 Go"}),
            "datacenter": forms.TextInput(
                attrs={
                    "class": "field-input",
                    "placeholder": "DC Tunis",
                    "data-validate": "max:255",
                }
            ),
            "server_type": forms.Select(
                attrs={"class": "field-input", "data-validate": "required"}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "field-check"}),
            "notes": forms.Textarea(
                attrs={"class": "field-input", "rows": 3, "data-validate": "max:5000"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
        self.fields["ip_address"].required = True
        self.fields["server_type"].required = True

    def clean_name(self):
        name = validate_server_name(self.cleaned_data.get("name"))
        qs = Server.objects.filter(name__iexact=name, is_deleted=False)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Un serveur avec ce nom existe déjà.")
        return name

    def clean_ip_address(self):
        ip = require_non_empty(str(self.cleaned_data.get("ip_address") or ""), "L'adresse IP")
        qs = Server.objects.filter(ip_address=ip, is_deleted=False)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Cette adresse IP est déjà attribuée à un autre serveur.")
        return ip

    def clean_cpu(self):
        return validate_resource_label(self.cleaned_data.get("cpu"), "CPU")

    def clean_ram(self):
        return validate_resource_label(self.cleaned_data.get("ram"), "RAM")
