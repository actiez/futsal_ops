from django.shortcuts import redirect

class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        if not request.user.is_staff:
            return redirect("player_home")

        return super().dispatch(request, *args, **kwargs)