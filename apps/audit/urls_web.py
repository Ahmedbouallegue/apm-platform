from django.urls import path

from apps.audit.views.web import AuditLogDetailView, AuditLogListView

app_name = "audit"

urlpatterns = [
    path("audit/", AuditLogListView.as_view(), name="list"),
    path("audit/<int:pk>/", AuditLogDetailView.as_view(), name="detail"),
]
