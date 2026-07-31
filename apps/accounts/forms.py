from django.contrib.auth.forms import AuthenticationForm
from django import forms

from apps.accounts.models import User


class BrandAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Identifiant",
        widget=forms.TextInput(
            attrs={
                "class": "field-input",
                "placeholder": "Identifiant",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "field-input",
                "placeholder": "Mot de passe",
                "autocomplete": "current-password",
            }
        ),
    )


class UserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Mot de passe",
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "field-input"}),
    )
    password2 = forms.CharField(
        label="Confirmation",
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "field-input"}),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone",
            "department",
            "is_active",
            "is_staff",
        )
        widgets = {
            "username": forms.TextInput(attrs={"class": "field-input"}),
            "email": forms.EmailInput(attrs={"class": "field-input"}),
            "first_name": forms.TextInput(attrs={"class": "field-input"}),
            "last_name": forms.TextInput(attrs={"class": "field-input"}),
            "role": forms.Select(attrs={"class": "field-input"}),
            "phone": forms.TextInput(attrs={"class": "field-input"}),
            "department": forms.TextInput(attrs={"class": "field-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "field-check"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "field-check"}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Les mots de passe ne correspondent pas.")
        return cleaned


class UserUpdateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Nouveau mot de passe",
        required=False,
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "field-input", "placeholder": "Laisser vide pour conserver"}),
    )
    password2 = forms.CharField(
        label="Confirmation",
        required=False,
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "field-input"}),
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "role",
            "phone",
            "department",
            "is_active",
            "is_staff",
        )
        widgets = {
            "email": forms.EmailInput(attrs={"class": "field-input"}),
            "first_name": forms.TextInput(attrs={"class": "field-input"}),
            "last_name": forms.TextInput(attrs={"class": "field-input"}),
            "role": forms.Select(attrs={"class": "field-input"}),
            "phone": forms.TextInput(attrs={"class": "field-input"}),
            "department": forms.TextInput(attrs={"class": "field-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "field-check"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "field-check"}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1") or ""
        p2 = cleaned.get("password2") or ""
        if p1 or p2:
            if p1 != p2:
                self.add_error("password2", "Les mots de passe ne correspondent pas.")
        return cleaned
