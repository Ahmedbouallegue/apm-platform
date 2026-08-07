from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.documents.views.api import DocumentViewSet, HealthView, TagViewSet

router = DefaultRouter()
router.register("tags", TagViewSet, basename="tag")
router.register("", DocumentViewSet, basename="document")

urlpatterns = [
    path("health/", HealthView.as_view(), name="documents-health"),
    *router.urls,
]
