from django.urls import path

from apps.accounts.forms import BrandAuthenticationForm
from apps.accounts.views.web import (
    BrandLoginView,
    BrandPasswordResetCompleteView,
    BrandPasswordResetConfirmView,
    BrandPasswordResetDoneView,
    BrandPasswordResetView,
    HomeView,
    ProfileView,
    UserCreateView,
    UserExportCsvView,
    UserImportCsvView,
    UserListView,
    UserToggleActiveView,
    UserUpdateView,
    logout_view,
)

app_name = "web"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path(
        "login/",
        BrandLoginView.as_view(authentication_form=BrandAuthenticationForm),
        name="login",
    ),
    path("logout/", logout_view, name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path(
        "password-reset/",
        BrandPasswordResetView.as_view(),
        name="password-reset",
    ),
    path(
        "password-reset/done/",
        BrandPasswordResetDoneView.as_view(),
        name="password-reset-done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        BrandPasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "password-reset/complete/",
        BrandPasswordResetCompleteView.as_view(),
        name="password-reset-complete",
    ),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/export.csv", UserExportCsvView.as_view(), name="user-export-csv"),
    path("users/import/", UserImportCsvView.as_view(), name="user-import-csv"),
    path("users/new/", UserCreateView.as_view(), name="user-create"),
    path("users/<int:pk>/edit/", UserUpdateView.as_view(), name="user-edit"),
    path("users/<int:pk>/toggle/", UserToggleActiveView.as_view(), name="user-toggle"),
]
