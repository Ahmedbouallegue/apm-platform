from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.contracts.views.api import ContractViewSet, HealthView

router = DefaultRouter()
router.register("", ContractViewSet, basename="contract")

urlpatterns = [
    path("health/", HealthView.as_view(), name="contracts-health"),
    *router.urls,
]
