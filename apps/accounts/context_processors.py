from apps.accounts.roles import (
    can_configure_platform,
    can_manage_users,
    can_write_patrimoine,
    can_write_users,
)


def access_flags(request):
    """Expose role-based flags to templates (nav, CTA)."""
    user = request.user
    return {
        "can_manage_users": can_manage_users(user),
        "can_write_users": can_write_users(user),
        "can_write_patrimoine": can_write_patrimoine(user),
        "can_configure_platform": can_configure_platform(user),
    }
