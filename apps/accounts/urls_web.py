from django.urls import path

from apps.accounts.forms import BrandAuthenticationForm
from apps.accounts.views.web import (
    BrandLoginView,
    HomeView,
    UserCreateView,
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
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/new/", UserCreateView.as_view(), name="user-create"),
    path("users/<int:pk>/edit/", UserUpdateView.as_view(), name="user-edit"),
    path("users/<int:pk>/toggle/", UserToggleActiveView.as_view(), name="user-toggle"),
]
