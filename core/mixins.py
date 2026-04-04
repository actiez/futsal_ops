from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_admin_level():
            raise PermissionDenied("You do not have admin access")
        return super().dispatch(request, *args, **kwargs)


class SuperadminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superadmin_level():
            raise PermissionDenied("You do not have superadmin access")
        return super().dispatch(request, *args, **kwargs)