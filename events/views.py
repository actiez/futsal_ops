from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render

from core.mixins import AdminRequiredMixin
from .models import Event
from .forms import EventForm
from system_settings.models import SystemSettings
from registrations.models import EventRegistration, EventStatusLog


class EventListView(AdminRequiredMixin, ListView):
    model = Event
    template_name = "events/list.html"
    context_object_name = "events"
    ordering = ["-start_datetime"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()
        return context


class EventCreateView(AdminRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "events/create.html"
    success_url = reverse_lazy("event_list")

    def get_initial(self):
        initial = super().get_initial()
        settings_obj = SystemSettings.get_solo()

        initial.update({
            "location": settings_obj.default_location,
            "amount_payable": settings_obj.default_amount_payable,
            "playing_slots": settings_obj.default_playing_slots,
            "waiting_slots": settings_obj.default_waiting_slots,
        })

        if settings_obj.default_start_time:
            initial["start_time"] = settings_obj.default_start_time
        if settings_obj.default_end_time:
            initial["end_time"] = settings_obj.default_end_time

        return initial

    def form_valid(self, form):
        start_datetime = form.cleaned_data["start_datetime"]
        location = form.cleaned_data["location"]

        duplicate_exists = Event.objects.filter(
            start_datetime=start_datetime,
            location=location,
        ).exists()

        if duplicate_exists:
            form.add_error(None, "An event already exists for this slot and location.")
            return self.form_invalid(form)

        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
class EventDetailView(AdminRequiredMixin, DetailView):
    model = Event
    template_name = "events/detail.html"
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object

        join_url = self.request.build_absolute_uri(
        reverse("join_event", kwargs={"token": event.registration_token})
)

        registrations = event.registrations.select_related("user").order_by("sequence_number")

        interested_regs = registrations.filter(status=EventRegistration.STATUS_INTERESTED)
        playing_regs = registrations.filter(status=EventRegistration.STATUS_PLAYING)
        waiting_regs = registrations.filter(status=EventRegistration.STATUS_WAITING)
        backup_regs = registrations.filter(status=EventRegistration.STATUS_BACKUP)

        context["interested_regs"] = interested_regs
        context["playing_regs"] = playing_regs
        context["waiting_regs"] = waiting_regs
        context["backup_regs"] = backup_regs

        context["playing_full"] = playing_regs.count() >= event.playing_slots
        context["waiting_full"] = waiting_regs.count() >= event.waiting_slots

        playing_lines = [
            f"{idx}. {reg.user.get_full_name() or reg.user.username}"
            for idx, reg in enumerate(playing_regs, start=1)
        ]

        waiting_lines = [
            f"{idx}. {reg.user.get_full_name() or reg.user.username}"
            for idx, reg in enumerate(waiting_regs, start=1)
        ]

        full_summary_lines = [
            "⚽ Futsal Session",
            "",
            f"{event.weekday_display}, {event.date_display}",
            event.time_range_display,
            event.location,
            f"${event.amount_payable} per pax",
            "",
            "Register here:",
            join_url,
            "",
            f"Playing ({playing_regs.count()}):",
        ]

        full_summary_lines.extend(playing_lines or ["-"])
        full_summary_lines.extend([
            "",
            f"Waiting List ({waiting_regs.count()}):",
        ])
        full_summary_lines.extend(waiting_lines or ["-"])

        reminder_summary_lines = [
            "⚽ Futsal Reminder",
            "",
            f"{event.weekday_display}, {event.date_display}",
            event.time_range_display,
            event.location,
            "",
            f"Playing ({playing_regs.count()}):",
        ]

        reminder_summary_lines.extend(playing_lines or ["-"])

        context["whatsapp_summary"] = "\n".join(full_summary_lines)
   
        invite_lines = [
            "⚽ Futsal Session",
            "",
            f"{event.weekday_display}, {event.date_display}",
            event.time_range_display,
            event.location,
            f"${event.amount_payable} per pax",
            "",
            "Join here:",
            join_url,
        ]

        context["invite_text"] = "\n".join(invite_lines)

        context["whatsapp_reminder_summary"] = "\n".join(reminder_summary_lines)
        context["join_url"] = join_url

        context["status_logs"] = (
            EventStatusLog.objects
            .filter(registration__event=event)
            .select_related("registration__user", "changed_by")
            .order_by("-changed_at")[:10]
        )

        context["registration_closed"] = timezone.now() >= event.start_datetime
        
        return context


class EventUpdateView(AdminRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "events/edit.html"

    def get_success_url(self):
        return reverse("event_detail", kwargs={"pk": self.object.pk})
    
    
class EventDeleteView(AdminRequiredMixin, DeleteView):
    model = Event
    template_name = "events/delete.html"
    success_url = reverse_lazy("event_list")