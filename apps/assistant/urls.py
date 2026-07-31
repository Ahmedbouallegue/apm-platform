from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.assistant.views.api import (
    AskView,
    ChatSessionViewSet,
    HealthView,
    ManualKnowledgeViewSet,
    ReindexView,
)

router = DefaultRouter()
router.register("sessions", ChatSessionViewSet, basename="assistant-session")
router.register("notes", ManualKnowledgeViewSet, basename="assistant-note")

urlpatterns = [
    path("health/", HealthView.as_view(), name="assistant-health"),
    path("ask/", AskView.as_view(), name="assistant-ask"),
    path("reindex/", ReindexView.as_view(), name="assistant-reindex"),
    *router.urls,
]
