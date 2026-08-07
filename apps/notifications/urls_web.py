from django.urls import path

from apps.notifications.views.web import (
    NotificationDetailView,
    NotificationListView,
    NotificationMarkReadView,
    PlatformSettingsView,
)

app_name = "notifications"

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="list"),
    path("notifications/<int:pk>/", NotificationDetailView.as_view(), name="detail"),
    path("notifications/<int:pk>/read/", NotificationMarkReadView.as_view(), name="mark_read"),
    path("settings/", PlatformSettingsView.as_view(), name="settings"),
]
