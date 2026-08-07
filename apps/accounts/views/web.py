from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from apps.accounts.forms import (
    BrandPasswordResetForm,
    BrandSetPasswordForm,
    ProfileForm,
    UserCreateForm,
    UserCsvImportForm,
    UserUpdateForm,
)
from apps.accounts.models import User
from apps.accounts.roles import (
    ROLE_DESCRIPTIONS,
    can_manage_users,
    can_write_patrimoine,
    can_write_users,
)
from apps.accounts.selectors.users import user_list
from apps.accounts.services.csv_users import users_from_csv, users_to_csv
from apps.accounts.services.face_auth import (
    FaceAuthError,
    authenticate_by_face,
    clear_face,
    enroll_face,
    user_has_face,
)
from apps.accounts.services.users import user_activate, user_create, user_deactivate, user_update
from apps.notifications.services.notifications import notify_user_login


def _can_manage_users(user) -> bool:
    return can_manage_users(user)


def _can_write_users(user) -> bool:
    return can_write_users(user)


def _can_write_apps(user) -> bool:
    return can_write_patrimoine(user)


def _client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or "unknown"


def _after_login(request, user, *, method: str = "password") -> None:
    from apps.audit.services.audit import audit_log_create

    notify_user_login(user=user, method=method)
    audit_log_create(
        action="login",
        entity="User",
        entity_id=user.pk,
        details=f"Connexion réussie ({method})",
        user=user,
        ip_address=_client_ip(request),
    )
    display = user.get_full_name() or user.get_username()
    messages.success(
        request,
        f"Bienvenue {display} — connexion réussie. Une notification a été enregistrée.",
    )


class BrandLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        _after_login(self.request, self.request.user, method="password")
        return response

    def get_success_url(self):
        return reverse_lazy("web:home")


class BrandPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/email/password_reset_email.txt"
    html_email_template_name = "accounts/email/password_reset_email.html"
    subject_template_name = "accounts/email/password_reset_subject.txt"
    form_class = BrandPasswordResetForm
    success_url = reverse_lazy("web:password-reset-done")
    extra_email_context = {"brand": "Topnet APM"}


class BrandPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class BrandPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = BrandSetPasswordForm
    success_url = reverse_lazy("web:password-reset-complete")


class BrandPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


def logout_view(request):
    from apps.audit.services.audit import audit_log_create

    user = request.user if request.user.is_authenticated else None
    if user:
        audit_log_create(
            action="logout",
            entity="User",
            entity_id=user.pk,
            details="Déconnexion",
            user=user,
            ip_address=_client_ip(request),
        )
    logout(request)
    messages.info(request, "Session terminée.")
    return redirect("web:login")


@method_decorator(login_required, name="dispatch")
class HomeView(View):
    def get(self, request):
        from apps.dashboard.selectors.dashboard import dashboard_stats

        stats = dashboard_stats(user=request.user)
        return render(
            request,
            "accounts/home.html",
            {
                "stats": stats,
                "charts_json": stats.get("charts") or {},
                "can_write": _can_write_apps(request.user),
                "is_viewer": (
                    request.user.is_authenticated
                    and request.user.role == User.Role.VIEWER
                    and not request.user.is_superuser
                ),
            },
        )


@method_decorator(login_required, name="dispatch")
class ProfileView(View):
    template_name = "accounts/profile.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "form": ProfileForm(instance=request.user),
                "face_enrolled": user_has_face(user=request.user),
            },
        )

    def post(self, request):
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            data = form.cleaned_data
            password = data.pop("password1", "") or None
            data.pop("password2", None)
            if password:
                data["password"] = password
            user_update(user=request.user, data=data, actor=request.user)
            messages.success(request, "Profil mis à jour.")
            return redirect("web:profile")
        return render(
            request,
            self.template_name,
            {"form": form, "face_enrolled": user_has_face(user=request.user)},
        )


def _face_login_rate_limited(request) -> bool:
    key = f"face_login_attempts:{_client_ip(request)}"
    attempts = cache.get(key, 0)
    max_attempts = int(getattr(settings, "FACE_LOGIN_MAX_ATTEMPTS", 10))
    return attempts >= max_attempts


def _face_login_register_attempt(request) -> None:
    key = f"face_login_attempts:{_client_ip(request)}"
    lockout = int(getattr(settings, "FACE_LOGIN_LOCKOUT_SECONDS", 300))
    attempts = cache.get(key, 0) + 1
    cache.set(key, attempts, timeout=lockout)


def _face_login_clear_attempts(request) -> None:
    cache.delete(f"face_login_attempts:{_client_ip(request)}")


def _parse_descriptor(request):
    try:
        import json

        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, ValueError):
        return None
    descriptor = payload.get("descriptor")
    if not isinstance(descriptor, list):
        return None
    return descriptor


@login_required
@require_POST
def face_enroll_view(request):
    descriptor = _parse_descriptor(request)
    if descriptor is None:
        return JsonResponse({"ok": False, "error": "Requête invalide."}, status=400)
    try:
        enroll_face(user=request.user, descriptor=descriptor)
    except FaceAuthError as exc:
        return JsonResponse({"ok": False, "error": exc.messages[0]}, status=400)
    return JsonResponse({"ok": True, "message": "Visage enregistré avec succès."})


@login_required
@require_POST
def face_clear_view(request):
    clear_face(user=request.user)
    return JsonResponse({"ok": True, "message": "Identifiant facial retiré."})


@require_POST
def face_login_view(request):
    if request.user.is_authenticated:
        return JsonResponse({"ok": True, "redirect": reverse("web:home")})

    if _face_login_rate_limited(request):
        return JsonResponse(
            {
                "ok": False,
                "error": "Trop de tentatives. Réessayez dans quelques minutes.",
            },
            status=429,
        )

    descriptor = _parse_descriptor(request)
    if descriptor is None:
        _face_login_register_attempt(request)
        return JsonResponse({"ok": False, "error": "Requête invalide."}, status=400)

    try:
        user = authenticate_by_face(descriptor)
    except FaceAuthError as exc:
        _face_login_register_attempt(request)
        return JsonResponse({"ok": False, "error": exc.messages[0]}, status=400)

    if user is None:
        _face_login_register_attempt(request)
        return JsonResponse(
            {"ok": False, "error": "Visage non reconnu. Réessayez ou utilisez le mot de passe."},
            status=401,
        )

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    _face_login_clear_attempts(request)
    _after_login(request, user, method="face")
    return JsonResponse({"ok": True, "redirect": reverse("web:home")})


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_manage_users), name="dispatch")
class UserListView(ListView):
    template_name = "accounts/users/list.html"
    context_object_name = "users"
    paginate_by = 15

    def get_queryset(self):
        search = self.request.GET.get("q") or None
        role = self.request.GET.get("role") or None
        active = self.request.GET.get("active")
        is_active = None
        if active == "1":
            is_active = True
        elif active == "0":
            is_active = False
        return user_list(search=search, role=role, is_active=is_active)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["roles"] = User.Role.choices
        ctx["q"] = self.request.GET.get("q", "")
        ctx["role"] = self.request.GET.get("role", "")
        ctx["active"] = self.request.GET.get("active", "")
        ctx["can_write"] = _can_write_users(self.request.user)
        ctx["role_descriptions"] = ROLE_DESCRIPTIONS
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_manage_users), name="dispatch")
class UserExportCsvView(View):
    def get(self, request):
        search = request.GET.get("q") or None
        role = request.GET.get("role") or None
        active = request.GET.get("active")
        is_active = None
        if active == "1":
            is_active = True
        elif active == "0":
            is_active = False
        users = user_list(search=search, role=role, is_active=is_active)
        payload = users_to_csv(users)
        stamp = timezone.localdate().isoformat()
        response = HttpResponse(payload, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="utilisateurs-apm-{stamp}.csv"'
        return response


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write_users), name="dispatch")
class UserImportCsvView(View):
    template_name = "accounts/users/import.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": UserCsvImportForm()},
        )

    def post(self, request):
        form = UserCsvImportForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        uploaded = form.cleaned_data["file"]
        try:
            content = uploaded.read()
            result = users_from_csv(content=content, actor=request.user)
        except UnicodeDecodeError:
            messages.error(request, "Encodage du fichier invalide. Utilisez UTF-8.")
            return render(request, self.template_name, {"form": form})

        if result.errors:
            for err in result.errors[:20]:
                messages.error(request, err)
            if len(result.errors) > 20:
                messages.error(request, f"… et {len(result.errors) - 20} autre(s) erreur(s).")
            return render(request, self.template_name, {"form": form})

        messages.success(
            request,
            f"Import terminé : {result.created} créé(s), {result.updated} mis à jour"
            + (f", {result.skipped} ligne(s) vide(s) ignorée(s)." if result.skipped else "."),
        )
        return redirect("web:user-list")


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write_users), name="dispatch")
class UserCreateView(View):
    template_name = "accounts/users/form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": UserCreateForm(), "title": "Nouvel utilisateur", "mode": "create"},
        )

    def post(self, request):
        form = UserCreateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            password = data.pop("password1")
            data.pop("password2", None)
            user_create(password=password, actor=request.user, **data)
            messages.success(request, "Utilisateur créé avec succès.")
            return redirect("web:user-list")
        return render(
            request,
            self.template_name,
            {"form": form, "title": "Nouvel utilisateur", "mode": "create"},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write_users), name="dispatch")
class UserUpdateView(View):
    template_name = "accounts/users/form.html"

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = UserUpdateForm(instance=user)
        return render(
            request,
            self.template_name,
            {"form": form, "title": f"Modifier — {user.username}", "mode": "edit", "user_obj": user},
        )

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            data = form.cleaned_data
            password = data.pop("password1", "") or None
            data.pop("password2", None)
            if password:
                data["password"] = password
            user_update(user=user, data=data, actor=request.user)
            messages.success(request, "Utilisateur mis à jour.")
            return redirect("web:user-list")
        return render(
            request,
            self.template_name,
            {"form": form, "title": f"Modifier — {user.username}", "mode": "edit", "user_obj": user},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write_users), name="dispatch")
class UserToggleActiveView(View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.pk == request.user.pk:
            messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
            return redirect("web:user-list")
        if user.is_active:
            user_deactivate(user=user, actor=request.user)
            messages.warning(request, f"Compte « {user.username} » désactivé.")
        else:
            user_activate(user=user, actor=request.user)
            messages.success(request, f"Compte « {user.username} » réactivé.")
        return redirect("web:user-list")
