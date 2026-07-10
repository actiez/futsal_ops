from django.shortcuts import redirect
from django.contrib import messages


class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        if not request.user.is_admin_level():
            return redirect("player_home")

        return super().dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        if not request.user.is_superadmin_level():
            messages.error(request, "Only superadmins can access user details.")
            return redirect("event_list")

        return super().dispatch(request, *args, **kwargs)