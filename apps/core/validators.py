"""Règles de validation métier partagées (formulaires + API)."""
from __future__ import annotations

import re
from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, URLValidator

PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-()]{6,20}$")
USERNAME_RE = re.compile(r"^[a-zA-Z0-9._-]{3,150}$")
SERVER_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{1,253}$")
VERSION_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._+\-]{0,63}$")
RESOURCE_RE = re.compile(r"^[0-9]+(\s?[a-zA-Z%]+)?$|^[0-9]+(\.[0-9]+)?\s?(v?CPU|Go|GB|Mo|MB|cores?)?$", re.I)
PASSWORD_COMPLEXITY_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")


def require_non_empty(value: str | None, label: str = "Ce champ") -> str:
    text = (value or "").strip()
    if not text:
        raise ValidationError(f"{label} est obligatoire.")
    return text


def validate_username(value: str) -> str:
    text = require_non_empty(value, "L'identifiant")
    if not USERNAME_RE.match(text):
        raise ValidationError(
            "Identifiant invalide (3–150 caractères : lettres, chiffres, . _ -)."
        )
    return text


def validate_email_required(value: str | None) -> str:
    text = require_non_empty(value, "L'email")
    EmailValidator(message="Adresse email invalide.")(text)
    return text.lower()


def validate_phone(value: str | None, *, required: bool = False) -> str:
    text = (value or "").strip()
    if not text:
        if required:
            raise ValidationError("Le téléphone est obligatoire.")
        return ""
    if not PHONE_RE.match(text):
        raise ValidationError(
            "Téléphone invalide. Exemple : +216 71 000 000 ou 71234567."
        )
    return text


def validate_password_strength(value: str | None) -> str:
    text = value or ""
    if len(text) < 8:
        raise ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
    if not PASSWORD_COMPLEXITY_RE.match(text):
        raise ValidationError(
            "Le mot de passe doit contenir au moins une lettre et un chiffre."
        )
    return text


def validate_optional_url(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    validator = URLValidator(schemes=["http", "https"], message="URL invalide (http/https).")
    validator(text)
    return text


def validate_version(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if not VERSION_RE.match(text):
        raise ValidationError("Version invalide (ex. 16, 5.2.1, 1.0.0-rc1).")
    return text


def validate_server_name(value: str) -> str:
    text = require_non_empty(value, "Le nom du serveur")
    if not SERVER_NAME_RE.match(text):
        raise ValidationError(
            "Nom de serveur invalide (lettres, chiffres, . _ - ; commencer par alphanumérique)."
        )
    return text


def validate_resource_label(value: str | None, label: str = "Valeur") -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if len(text) > 64:
        raise ValidationError(f"{label} trop long (max 64 caractères).")
    return text


def validate_date_range(
    start: date | None,
    end: date | None,
    *,
    start_label: str = "Date de début",
    end_label: str = "Date de fin",
) -> None:
    if start and end and end < start:
        raise ValidationError(
            f"{end_label} doit être postérieure ou égale à {start_label.lower()}."
        )


def validate_app_name(value: str) -> str:
    text = require_non_empty(value, "Le nom de l'application")
    if len(text) < 2:
        raise ValidationError("Le nom doit contenir au moins 2 caractères.")
    if len(text) > 255:
        raise ValidationError("Le nom ne peut pas dépasser 255 caractères.")
    return text


def validate_tech_name(value: str) -> str:
    text = require_non_empty(value, "Le nom de la technologie")
    if len(text) < 2:
        raise ValidationError("Le nom doit contenir au moins 2 caractères.")
    return text
