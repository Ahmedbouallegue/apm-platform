from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.accounts.decorators import user_passes_test_or_403
from apps.accounts.roles import can_configure_platform, can_read, is_admin_dsi
from apps.notifications.forms import PlatformSettingsForm
from apps.notifications.models import Notification, PlatformSettings
from apps.notifications.selectors.notifications import notification_list
from apps.notifications.services.notifications import notification_mark_read


def _can_view(user) -> bool:
    return can_read(user)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class NotificationListView(ListView):
    template_name = "notifications/list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        filter_user = None if is_admin_dsi(user) else user
        return notification_list(
            user=filter_user,
            status=self.request.GET.get("status") or None,
            notification_type=self.request.GET.get("type") or None,
            search=self.request.GET.get("q") or None,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Notification.Status.choices
        ctx["types"] = Notification.NotificationType.choices
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status"] = self.request.GET.get("status", "")
        ctx["type"] = self.request.GET.get("type", "")
        ctx["is_admin_dsi"] = is_admin_dsi(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class NotificationDetailView(DetailView):
    template_name = "notifications/detail.html"
    context_object_name = "notification"

    def get_queryset(self):
        user = self.request.user
        filter_user = None if is_admin_dsi(user) else user
        return notification_list(user=filter_user)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class NotificationMarkReadView(View):
    def post(self, request, pk):
        user = request.user
        filter_user = None if is_admin_dsi(user) else user
        notification = get_object_or_404(notification_list(user=filter_user), pk=pk)
        notification_mark_read(notification=notification)
        messages.success(request, "Notification marquée comme lue.")
        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("notifications:detail", pk=notification.pk)


@method_decorator(login_required, name="dispatch")
@method_decorator(
    user_passes_test_or_403(can_configure_platform), name="dispatch"
)
class PlatformSettingsView(View):
    template_name = "notifications/settings.html"

    def get(self, request):
        settings_obj = PlatformSettings.load()
        return render(
            request,
            self.template_name,
            {
                "form": PlatformSettingsForm(instance=settings_obj),
                "settings_obj": settings_obj,
            },
        )

    def post(self, request):
        settings_obj = PlatformSettings.load()
        form = PlatformSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Paramètres globaux enregistrés. Les alertes Celery utiliseront ces seuils.",
            )
            return redirect("notifications:settings")
        return render(
            request,
            self.template_name,
            {"form": form, "settings_obj": settings_obj},
        )
