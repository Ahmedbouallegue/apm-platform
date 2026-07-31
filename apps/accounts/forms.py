from email.mime.image import MIMEImage

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template import loader

from apps.accounts.models import User
from apps.core.validators import (
    validate_email_required,
    validate_password_strength,
    validate_phone,
    validate_username,
)


class BrandAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Identifiant",
        min_length=3,
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "field-input",
                "placeholder": "Identifiant",
                "autocomplete": "username",
                "data-validate": "required|username",
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
                "data-validate": "required|min:8",
            }
        ),
    )


class BrandPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Adresse email",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "class": "field-input",
                "placeholder": "ex. prenom.nom@topnet.tn",
                "autocomplete": "email",
                "data-validate": "required|email",
            }
        ),
    )

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """Envoie l'email avec le logo Topnet intégré pour les clients mail."""
        subject = loader.render_to_string(subject_template_name, context)
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)
        message = EmailMultiAlternatives(subject, body, from_email, [to_email])

        if html_email_template_name:
            html_body = loader.render_to_string(html_email_template_name, context)
            message.attach_alternative(html_body, "text/html")

            logo_path = settings.BASE_DIR / "static" / "branding" / "logo-topnet.png"
            if logo_path.exists():
                logo = MIMEImage(logo_path.read_bytes(), _subtype="png")
                logo.add_header("Content-ID", "<topnet-logo>")
                logo.add_header(
                    "Content-Disposition",
                    "inline",
                    filename="logo-topnet.png",
                )
                message.attach(logo)
                message.mixed_subtype = "related"

        message.send()


class BrandSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "field-input",
                "autocomplete": "new-password",
                "data-validate": "required|password",
            }
        ),
    )
    new_password2 = forms.CharField(
        label="Confirmation",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "field-input",
                "autocomplete": "new-password",
                "data-validate": "required|match:new_password1",
            }
        ),
    )

    def clean_new_password1(self):
        password = validate_password_strength(self.cleaned_data.get("new_password1"))
        validate_password(password, user=self.user)
        return password


class UserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Mot de passe",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "field-input",
                "autocomplete": "new-password",
                "data-validate": "required|password",
            }
        ),
        help_text="Min. 8 caractères, avec au moins une lettre et un chiffre.",
    )
    password2 = forms.CharField(
        label="Confirmation",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "field-input",
                "autocomplete": "new-password",
                "data-validate": "required|match:password1",
            }
        ),
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
            "username": forms.TextInput(
                attrs={"class": "field-input", "data-validate": "required|username"}
            ),
            "email": forms.TextInput(
                attrs={"class": "field-input", "data-validate": "required|email"}
            ),
            "first_name": forms.TextInput(attrs={"class": "field-input", "data-validate": "max:150"}),
            "last_name": forms.TextInput(attrs={"class": "field-input", "data-validate": "max:150"}),
            "role": forms.Select(attrs={"class": "field-input", "data-validate": "required"}),
            "phone": forms.TextInput(
                attrs={
                    "class": "field-input",
                    "placeholder": "+216 71 000 000",
                    "data-validate": "phone",
                }
            ),
            "department": forms.TextInput(attrs={"class": "field-input", "data-validate": "max:128"}),
            "is_active": forms.CheckboxInput(attrs={"class": "field-check"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "field-check"}),
        }

    def clean_username(self):
        username = validate_username(self.cleaned_data.get("username"))
        qs = User.objects.filter(username__iexact=username)
        if qs.exists():
            raise ValidationError("Cet identifiant est déjà utilisé.")
        return username

    def clean_email(self):
        email = validate_email_required(self.cleaned_data.get("email"))
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Cet email est déjà utilisé.")
        return email

    def clean_phone(self):
        return validate_phone(self.cleaned_data.get("phone"))

    def clean_password1(self):
        password = validate_password_strength(self.cleaned_data.get("password1"))
        validate_password(password)
        return password

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
        widget=forms.PasswordInput(
            attrs={
                "class": "field-input",
                "placeholder": "Laisser vide pour conserver",
                "autocomplete": "new-password",
                "data-validate": "password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirmation",
        required=False,
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "field-input",
                "autocomplete": "new-password",
                "data-validate": "match:password1",
            }
        ),
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
            "email": forms.TextInput(
                attrs={"class": "field-input", "data-validate": "required|email"}
            ),
            "first_name": forms.TextInput(attrs={"class": "field-input", "data-validate": "max:150"}),
            "last_name": forms.TextInput(attrs={"class": "field-input", "data-validate": "max:150"}),
            "role": forms.Select(attrs={"class": "field-input", "data-validate": "required"}),
            "phone": forms.TextInput(
                attrs={
                    "class": "field-input",
                    "placeholder": "+216 71 000 000",
                    "data-validate": "phone",
                }
            ),
            "department": forms.TextInput(attrs={"class": "field-input", "data-validate": "max:128"}),
            "is_active": forms.CheckboxInput(attrs={"class": "field-check"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "field-check"}),
        }

    def clean_email(self):
        email = validate_email_required(self.cleaned_data.get("email"))
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Cet email est déjà utilisé.")
        return email

    def clean_phone(self):
        return validate_phone(self.cleaned_data.get("phone"))

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1") or ""
        p2 = cleaned.get("password2") or ""
        if p1 or p2:
            if p1 != p2:
                self.add_error("password2", "Les mots de passe ne correspondent pas.")
            elif p1:
                try:
                    cleaned["password1"] = validate_password_strength(p1)
                    validate_password(cleaned["password1"], user=self.instance)
                except ValidationError as exc:
                    self.add_error("password1", exc)
        return cleaned
