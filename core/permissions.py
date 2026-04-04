def user_is_admin_level(user):
    return user.is_authenticated and user.role in ["admin", "superadmin"]


def user_is_superadmin(user):
    return user.is_authenticated and user.role == "superadmin"