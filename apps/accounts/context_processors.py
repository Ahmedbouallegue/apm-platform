from apps.accounts.roles import (
    can_configure_platform,
    can_manage_users,
    can_write_patrimoine,
    can_write_users,
    is_viewer,
)


def access_flags(request):
    """Expose role-based flags to templates (nav, CTA, boutons CRUD)."""
    user = request.user
    write_patrimoine = can_write_patrimoine(user)
    return {
        "can_manage_users": can_manage_users(user),
        "can_write_users": can_write_users(user),
        "can_write_patrimoine": write_patrimoine,
        # Alias utilisé par les templates list/detail métier
        "can_write": write_patrimoine,
        "can_configure_platform": can_configure_platform(user),
        "is_viewer": is_viewer(user),
    }
