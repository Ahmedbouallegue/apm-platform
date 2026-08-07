from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from apps.audit.selectors.audit import audit_log_list


def _can_view(user) -> bool:
    return bool(user.is_authenticated)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class AuditLogListView(ListView):
    template_name = "audit/list.html"
    context_object_name = "logs"
    paginate_by = 25

    def get_queryset(self):
        user_id = self.request.GET.get("user") or None
        return audit_log_list(
            search=self.request.GET.get("q") or None,
            action=self.request.GET.get("action") or None,
            entity=self.request.GET.get("entity") or None,
            user_id=int(user_id) if user_id and user_id.isdigit() else None,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["action"] = self.request.GET.get("action", "")
        ctx["entity"] = self.request.GET.get("entity", "")
        ctx["user"] = self.request.GET.get("user", "")
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class AuditLogDetailView(DetailView):
    template_name = "audit/detail.html"
    context_object_name = "log"

    def get_queryset(self):
        return audit_log_list()
