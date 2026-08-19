"""Auth helpers compatible Django 5.2+ (raise_exception retiré de user_passes_test)."""

from __future__ import annotations

from collections.abc import Callable

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def user_passes_test_or_403(test_func: Callable) -> Callable:
    """Comme user_passes_test, mais 403 si connecté et test échoué (pas redirect login)."""

    def _test(user):
        if test_func(user):
            return True
        if getattr(user, "is_authenticated", False):
            raise PermissionDenied
        return False

    return user_passes_test(_test)
