from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView

from apps.accounts.forms import UserCreateForm, UserUpdateForm
from apps.accounts.models import User
from apps.accounts.selectors.users import user_list
from apps.accounts.services.users import user_activate, user_create, user_deactivate, user_update


def _can_manage_users(user) -> bool:
    return bool(
        user.is_authenticated
        and (user.is_superuser or user.role in {User.Role.ADMIN, User.Role.DSI, User.Role.MANAGER})
    )


def _can_write_users(user) -> bool:
    return bool(
        user.is_authenticated
        and (user.is_superuser or user.role in {User.Role.ADMIN, User.Role.DSI})
    )


class BrandLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("web:home")


def logout_view(request):
    logout(request)
    messages.info(request, "Session terminée.")
    return redirect("web:login")


@method_decorator(login_required, name="dispatch")
class HomeView(View):
    def get(self, request):
        stats = {
            "users_total": User.objects.count(),
            "users_active": User.objects.filter(is_active=True).count(),
            "users_admin": User.objects.filter(role=User.Role.ADMIN).count(),
            "users_dsi": User.objects.filter(role=User.Role.DSI).count(),
        }
        return render(request, "accounts/home.html", {"stats": stats})


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
        return ctx


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
            user_create(password=password, **data)
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
            user_update(user=user, data=data)
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
            user_deactivate(user=user)
            messages.warning(request, f"Compte « {user.username} » désactivé.")
        else:
            user_activate(user=user)
            messages.success(request, f"Compte « {user.username} » réactivé.")
        return redirect("web:user-list")
