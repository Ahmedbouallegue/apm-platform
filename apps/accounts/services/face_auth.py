"""Facial recognition helpers: enroll, clear, authenticate by descriptor."""

from __future__ import annotations

import math
from typing import Sequence

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import FaceCredential, User


class FaceAuthError(ValidationError):
    """Raised when a face descriptor cannot be enrolled or matched."""


def _descriptor_size() -> int:
    return int(getattr(settings, "FACE_DESCRIPTOR_SIZE", 128))


def _match_threshold() -> float:
    return float(getattr(settings, "FACE_MATCH_THRESHOLD", 0.55))


def _ambiguity_margin() -> float:
    return float(getattr(settings, "FACE_AMBIGUITY_MARGIN", 0.05))


def normalize_descriptor(descriptor: Sequence[float]) -> list[float]:
    """Validate and coerce a face-api.js descriptor to a float list."""
    expected = _descriptor_size()
    if not isinstance(descriptor, (list, tuple)):
        raise FaceAuthError("Descripteur facial invalide.")
    if len(descriptor) != expected:
        raise FaceAuthError(f"Descripteur facial invalide (attendu {expected} dimensions).")
    try:
        values = [float(v) for v in descriptor]
    except (TypeError, ValueError) as exc:
        raise FaceAuthError("Descripteur facial invalide.") from exc
    if not all(math.isfinite(v) for v in values):
        raise FaceAuthError("Descripteur facial invalide.")
    return values


def euclidean_distance(a: Sequence[float], b: Sequence[float]) -> float:
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b, strict=True)))


@transaction.atomic
def enroll_face(*, user: User, descriptor: Sequence[float]) -> FaceCredential:
    values = normalize_descriptor(descriptor)
    credential, _created = FaceCredential.objects.update_or_create(
        user=user,
        defaults={
            "descriptor": values,
            "is_active": True,
            "enrolled_at": timezone.now(),
        },
    )
    return credential


@transaction.atomic
def clear_face(*, user: User) -> bool:
    deleted, _ = FaceCredential.objects.filter(user=user).delete()
    return deleted > 0


def user_has_face(*, user: User) -> bool:
    return FaceCredential.objects.filter(user=user, is_active=True).exists()


def authenticate_by_face(descriptor: Sequence[float]) -> User | None:
    """
    Return the best matching active user under the distance threshold.

    Rejects when no match, or when the two closest matches are too close
    (ambiguous identity).
    """
    probe = normalize_descriptor(descriptor)
    threshold = _match_threshold()
    margin = _ambiguity_margin()

    credentials = (
        FaceCredential.objects.filter(is_active=True, user__is_active=True)
        .select_related("user")
        .only("id", "descriptor", "user_id", "user__id", "user__is_active", "user__username")
    )

    scored: list[tuple[float, User]] = []
    for cred in credentials:
        try:
            stored = normalize_descriptor(cred.descriptor)
        except FaceAuthError:
            continue
        distance = euclidean_distance(probe, stored)
        if distance <= threshold:
            scored.append((distance, cred.user))

    if not scored:
        return None

    scored.sort(key=lambda item: item[0])
    best_distance, best_user = scored[0]
    if len(scored) > 1:
        second_distance, _ = scored[1]
        if (second_distance - best_distance) < margin:
            return None
    return best_user
