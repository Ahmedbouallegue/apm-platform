import json
import math
import re
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import FaceCredential
from apps.accounts.services.face_auth import (
    FaceAuthError,
    authenticate_by_face,
    clear_face,
    enroll_face,
    euclidean_distance,
    normalize_descriptor,
    user_has_face,
)

User = get_user_model()


def make_descriptor(seed: float = 0.1) -> list[float]:
    """Deterministic pseudo face-api descriptor (128 floats)."""
    values = []
    x = seed
    for i in range(128):
        x = math.sin(x * 12.9898 + i * 78.233) * 43758.5453
        values.append((x - math.floor(x)) * 2 - 1)
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


class FaceAuthServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="faceuser",
            password="Secret123!",
            role=User.Role.MANAGER,
        )
        self.descriptor = make_descriptor(0.2)

    def test_normalize_rejects_bad_length(self):
        with self.assertRaises(FaceAuthError):
            normalize_descriptor([0.1, 0.2])

    def test_enroll_and_authenticate(self):
        enroll_face(user=self.user, descriptor=self.descriptor)
        self.assertTrue(user_has_face(user=self.user))
        matched = authenticate_by_face(self.descriptor)
        self.assertEqual(matched, self.user)

    def test_authenticate_rejects_far_descriptor(self):
        enroll_face(user=self.user, descriptor=self.descriptor)
        other = make_descriptor(0.9)
        distance = euclidean_distance(self.descriptor, other)
        self.assertGreater(distance, 0.55)
        self.assertIsNone(authenticate_by_face(other))

    def test_clear_face(self):
        enroll_face(user=self.user, descriptor=self.descriptor)
        self.assertTrue(clear_face(user=self.user))
        self.assertFalse(user_has_face(user=self.user))
        self.assertIsNone(authenticate_by_face(self.descriptor))

    def test_ambiguous_match_rejected(self):
        other = User.objects.create_user(
            username="faceuser2",
            password="Secret123!",
            role=User.Role.VIEWER,
        )
        base = make_descriptor(0.3)
        # Nearly identical descriptors for two users
        near = list(base)
        near[0] = base[0] + 0.01
        enroll_face(user=self.user, descriptor=base)
        enroll_face(user=other, descriptor=near)
        probe = list(base)
        probe[0] = base[0] + 0.005
        self.assertIsNone(authenticate_by_face(probe))


class FaceAuthWebTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            username="webface",
            password="Secret123!",
            role=User.Role.DSI,
        )
        self.descriptor = make_descriptor(0.4)

    def _csrf_token(self, path: Optional[str] = None) -> str:
        response = self.client.get(path or reverse("web:login"))
        self.assertIn(response.status_code, {200, 302})
        if "csrftoken" in self.client.cookies:
            return self.client.cookies["csrftoken"].value
        match = re.search(
            rb'name="csrfmiddlewaretoken" value="([^"]+)"',
            getattr(response, "content", b""),
        )
        if match:
            return match.group(1).decode()
        self.fail("CSRF token introuvable")

    def test_login_page_has_face_tab(self):
        response = self.client.get(reverse("web:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-auth-tab="face"')
        self.assertContains(response, "face-auth.js")

    def test_profile_shows_biometric_section(self):
        self.client.login(username="webface", password="Secret123!")
        response = self.client.get(reverse("web:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sécurité biométrique")
        self.assertContains(response, "Non enrôlé")

    def test_enroll_and_face_login(self):
        self.client.login(username="webface", password="Secret123!")
        token = self._csrf_token(reverse("web:profile"))

        enroll = self.client.post(
            reverse("web:face-enroll"),
            data=json.dumps({"descriptor": self.descriptor}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(enroll.status_code, 200)
        self.assertTrue(enroll.json()["ok"])
        self.assertTrue(FaceCredential.objects.filter(user=self.user, is_active=True).exists())

        self.client.logout()
        token = self._csrf_token(reverse("web:login"))
        response = self.client.post(
            reverse("web:login-face"),
            data=json.dumps({"descriptor": self.descriptor}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["redirect"], reverse("web:home"))

    def test_face_login_unknown(self):
        token = self._csrf_token()
        response = self.client.post(
            reverse("web:login-face"),
            data=json.dumps({"descriptor": self.descriptor}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["ok"])

    @override_settings(FACE_LOGIN_MAX_ATTEMPTS=2, FACE_LOGIN_LOCKOUT_SECONDS=300)
    def test_face_login_rate_limit(self):
        token = self._csrf_token()
        body = json.dumps({"descriptor": self.descriptor})
        for _ in range(2):
            self.client.post(
                reverse("web:login-face"),
                data=body,
                content_type="application/json",
                HTTP_X_CSRFTOKEN=token,
            )
        response = self.client.post(
            reverse("web:login-face"),
            data=body,
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 429)
