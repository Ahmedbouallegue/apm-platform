from apps.accounts.roles import (
    can_configure_platform,
    can_manage_users,
    can_read_infrastructure,
    can_read_patrimoine,
    can_write_infrastructure,
    can_write_patrimoine,
    can_write_users,
    is_admin_system,
)


def access_flags(request):
    """Expose role-based flags to templates (nav, CTA, boutons CRUD)."""
    user = request.user
    write_patrimoine = can_write_patrimoine(user)
    return {
        "can_manage_users": can_manage_users(user),
        "can_write_users": can_write_users(user),
        "can_read_patrimoine": can_read_patrimoine(user),
        "can_read_infrastructure": can_read_infrastructure(user),
        "can_write_patrimoine": write_patrimoine,
        "can_write_infrastructure": can_write_infrastructure(user),
        # Alias utilisés par les templates list/detail métier
        "can_write": write_patrimoine,
        "can_configure_platform": can_configure_platform(user),
        "is_admin_system": is_admin_system(user),
    }
