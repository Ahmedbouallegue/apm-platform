"""Serving sécurisé des fichiers media (auth obligatoire)."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.utils.decorators import method_decorator
from django.views import View

from apps.accounts.decorators import user_passes_test_or_403
from apps.accounts.roles import can_read


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test_or_403(can_read), name="dispatch")
class SecureMediaView(View):
    """Sert un fichier sous MEDIA_ROOT après contrôle anti path-traversal."""

    def get(self, request, path: str):
        media_root = Path(settings.MEDIA_ROOT).resolve()
        target = (media_root / path).resolve()
        if media_root not in target.parents and target != media_root:
            raise Http404("Fichier introuvable.")
        if not target.is_file():
            raise Http404("Fichier introuvable.")

        content_type, _ = mimetypes.guess_type(str(target))
        response = FileResponse(
            target.open("rb"),
            content_type=content_type or "application/octet-stream",
        )
        response["Content-Disposition"] = f'inline; filename="{target.name}"'
        return response
