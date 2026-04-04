from django.views.generic import TemplateView
from core.mixins import AdminRequiredMixin
from events.models import Event
from accounts.models import User
from django.utils import timezone


class DashboardView(AdminRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        context["upcoming_events_count"] = Event.objects.filter(start_datetime__gt=now).count()
        context["past_events_count"] = Event.objects.filter(end_datetime__lt=now).count()
        context["total_users_count"] = User.objects.count()
        context["recent_events"] = Event.objects.order_by("-start_datetime")[:5]

        return context