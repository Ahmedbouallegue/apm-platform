"""Import / export CSV des utilisateurs APM."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from dataclasses import dataclass, field

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.services.users import user_create, user_update

User = get_user_model()

CSV_HEADERS = (
    "username",
    "email",
    "first_name",
    "last_name",
    "role",
    "phone",
    "department",
    "is_active",
    "password",
)

ROLE_ALIASES = {
    "admin": User.Role.ADMIN,
    "administrateur": User.Role.ADMIN,
    "administrateur dsi": User.Role.ADMIN,
    "dsi": User.Role.DSI,
    "manager": User.Role.MANAGER,
    "technicien": User.Role.MANAGER,
    "equipe dsi": User.Role.MANAGER,
    "équipe dsi": User.Role.MANAGER,
    "viewer": User.Role.VIEWER,
    "lecteur": User.Role.VIEWER,
}


@dataclass
class UserCsvImportResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "oui", "y", "o", "actif", "active"}


def _normalize_role(raw: str) -> str:
    key = (raw or "").strip().lower()
    if not key:
        return User.Role.VIEWER
    if key in ROLE_ALIASES:
        return ROLE_ALIASES[key]
    valid = {c.value for c in User.Role}
    if key in valid:
        return key
    raise ValidationError(f"Rôle invalide « {raw} ».")


def users_to_csv(users: Iterable[User]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_HEADERS, lineterminator="\n")
    writer.writeheader()
    for user in users:
        writer.writerow(
            {
                "username": user.username,
                "email": user.email or "",
                "first_name": user.first_name or "",
                "last_name": user.last_name or "",
                "role": user.role,
                "phone": user.phone or "",
                "department": user.department or "",
                "is_active": "1" if user.is_active else "0",
                "password": "",
            }
        )
    return buffer.getvalue()


def _row_get(row: dict, *keys: str) -> str:
    lowered = {str(k).strip().lower(): v for k, v in row.items() if k is not None}
    for key in keys:
        if key in lowered and lowered[key] is not None:
            return str(lowered[key]).strip()
    return ""


@transaction.atomic
def users_from_csv(*, content: str | bytes, encoding: str = "utf-8-sig", actor=None) -> UserCsvImportResult:
    if isinstance(content, bytes):
        text = content.decode(encoding)
    else:
        text = content

    result = UserCsvImportResult()
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        result.errors.append("Fichier CSV vide ou sans en-têtes.")
        return result

    headers = {h.strip().lower() for h in reader.fieldnames if h}
    if "username" not in headers:
        result.errors.append("Colonne obligatoire manquante : username.")
        return result

    for index, row in enumerate(reader, start=2):
        username = _row_get(row, "username")
        if not username:
            result.skipped += 1
            continue

        try:
            role = _normalize_role(_row_get(row, "role"))
            email = _row_get(row, "email")
            first_name = _row_get(row, "first_name", "prenom", "prénom")
            last_name = _row_get(row, "last_name", "nom")
            phone = _row_get(row, "phone", "telephone", "téléphone")
            department = _row_get(row, "department", "departement", "département")
            active_raw = _row_get(row, "is_active", "active", "actif")
            is_active = _truthy(active_raw) if active_raw else True
            password = _row_get(row, "password", "mot_de_passe")

            existing = User.objects.filter(username=username).first()
            if existing:
                data = {
                    "email": email or existing.email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": role,
                    "phone": phone,
                    "department": department,
                    "is_active": is_active,
                }
                if password:
                    validate_password(password, user=existing)
                    data["password"] = password
                user_update(user=existing, data=data, actor=actor)
                result.updated += 1
            else:
                if not password:
                    raise ValidationError("Mot de passe obligatoire pour un nouvel utilisateur.")
                if not email:
                    raise ValidationError("Email obligatoire pour un nouvel utilisateur.")
                validate_password(password)
                user_create(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    phone=phone,
                    department=department,
                    is_active=is_active,
                    actor=actor,
                )
                result.created += 1
        except ValidationError as exc:
            messages = getattr(exc, "messages", None) or [str(exc)]
            for msg in messages:
                result.errors.append(f"Ligne {index} ({username}) : {msg}")
        except Exception as exc:  # noqa: BLE001 — surface row errors to the UI
            result.errors.append(f"Ligne {index} ({username}) : {exc}")

    if result.errors:
        # Roll back all changes if any row failed
        transaction.set_rollback(True)
        result.created = 0
        result.updated = 0

    return result
