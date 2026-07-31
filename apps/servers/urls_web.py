from django.urls import path

from apps.servers.views.web import (
    ServerCreateView,
    ServerDeleteView,
    ServerDetailView,
    ServerListView,
    ServerUpdateView,
)

app_name = "servers"

urlpatterns = [
    path("servers/", ServerListView.as_view(), name="list"),
    path("servers/new/", ServerCreateView.as_view(), name="create"),
    path("servers/<int:pk>/", ServerDetailView.as_view(), name="detail"),
    path("servers/<int:pk>/edit/", ServerUpdateView.as_view(), name="edit"),
    path("servers/<int:pk>/delete/", ServerDeleteView.as_view(), name="delete"),
]
