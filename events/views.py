from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views import View
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count

from core.mixins import AdminRequiredMixin
from system_settings.models import SystemSettings
from registrations.models import EventRegistration, EventStatusLog

from .forms import EventForm
from .models import Event, EventCloseout, EventAttendance
from .services import create_closeout_snapshot, event_is_closeout_eligible

class EventListView(ListView):
    model = Event
    template_name = "events/list.html"
    context_object_name = "events"
    ordering = ["-start_datetime"]

    def get_queryset(self):
        queryset = super().get_queryset()

        user = self.request.user

        if user.is_authenticated and user.is_admin_level():
            return queryset

        return queryset.filter(is_private=False)

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
            "backup_slots": getattr(settings_obj, "default_backup_slots", 3),
            "event_date": timezone.localdate(),
        })

        if settings_obj.default_start_time:
            initial["start_time"] = settings_obj.default_start_time.strftime("%H:%M")

        if settings_obj.default_end_time:
            initial["end_time"] = settings_obj.default_end_time.strftime("%H:%M")

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

        def whatsapp_mention_for_user(user):
            mobile = (user.mobile_number or "").strip()

            mobile = (
                mobile
                .replace("+", "")
                .replace(" ", "")
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
            )

            if mobile and mobile.isdigit():
                if mobile.startswith("65") and len(mobile) == 10:
                    mobile = mobile[2:]

                return f"@{mobile}"

            return ""
        
        playing_lines = [
            f"{idx}. {reg.user.get_full_name() or reg.user.username}"
            for idx, reg in enumerate(playing_regs, start=1)
        ]

        reminder_playing_lines = []

        for idx, reg in enumerate(playing_regs, start=1):
            display_name = reg.user.get_full_name() or reg.user.username
            mention = whatsapp_mention_for_user(reg.user)

            if mention:
                reminder_playing_lines.append(f"{idx}. {display_name} {mention}")
            else:
                reminder_playing_lines.append(f"{idx}. {display_name}")

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
            "Register/Leave Game here:",
            join_url,
            "",
            f"Playing ({playing_regs.count()}/{event.playing_slots}):",
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
            f"Playing ({playing_regs.count()}/{event.playing_slots}):",
        ]

        reminder_summary_lines.extend(reminder_playing_lines or ["-"])

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

        settings_obj = SystemSettings.get_solo()

        context["weekly_limit_enabled"] = settings_obj.only_allow_once_per_week_registration
        context["whatsapp_summary"] = "\n".join(full_summary_lines)
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

        closeout = EventCloseout.objects.filter(event=event).first()
        closeout_available = (
            event.end_datetime <= timezone.now()
            and event.status != Event.STATUS_CANCELLED
        )

        context["closeout"] = closeout
        context["closeout_available"] = closeout_available

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

class EventCloseoutView(AdminRequiredMixin, View):
    template_name = "events/closeout.html"

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=kwargs["pk"])

        if self.event.status == Event.STATUS_CANCELLED:
            messages.error(request, "Cancelled events do not require closeout.")
            return redirect("event_detail", pk=self.event.pk)

        if not event_is_closeout_eligible(self.event):
            messages.error(request, "Closeout is only available after the event has ended.")
            return redirect("event_detail", pk=self.event.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_closeout(self):
        return create_closeout_snapshot(self.event, created_by=self.request.user)

    def get_context_data(self, closeout):
        active_attendances = (
            closeout.attendances
            .filter(is_active=True)
            .select_related("user", "registration")
            .order_by("user__first_name", "user__last_name", "user__username")
        )

        active_user_ids = active_attendances.values_list("user_id", flat=True)

        User = get_user_model()
        available_users = (
            User.objects
            .exclude(id__in=active_user_ids)
            .order_by("first_name", "last_name", "username")
        )

        summary = {
            "attended": active_attendances.filter(status=EventAttendance.STATUS_ATTENDED).count(),
            "absent": active_attendances.filter(status=EventAttendance.STATUS_ABSENT).count(),
            "excused": active_attendances.filter(status=EventAttendance.STATUS_EXCUSED).count(),
            "total": active_attendances.count(),
        }

        return {
            "event": self.event,
            "closeout": closeout,
            "active_attendances": active_attendances,
            "available_users": available_users,
            "summary": summary,
            "attendance_status_choices": EventAttendance.STATUS_CHOICES,
        }

    def get(self, request, pk):
        closeout = self.get_closeout()

        return render(
            request,
            self.template_name,
            self.get_context_data(closeout),
        )

    def post(self, request, pk):
        closeout = self.get_closeout()

        if closeout.is_closed:
            messages.info(request, "This closeout is already closed and can only be viewed.")
            return redirect("event_closeout", pk=self.event.pk)

        action = request.POST.get("action")

        if action in {"save", "close"}:
            attendances = closeout.attendances.filter(is_active=True)

            for attendance in attendances:
                status_key = f"status_{attendance.id}"
                notes_key = f"notes_{attendance.id}"

                new_status = request.POST.get(status_key)
                new_notes = request.POST.get(notes_key, "")

                if new_status in {
                    EventAttendance.STATUS_ATTENDED,
                    EventAttendance.STATUS_ABSENT,
                    EventAttendance.STATUS_EXCUSED,
                }:
                    attendance.status = new_status

                attendance.notes = new_notes
                attendance.updated_by = request.user
                attendance.save()

            if action == "close":
                closeout.status = EventCloseout.STATUS_CLOSED_MANUAL
                closeout.closed_by = request.user
                closeout.closed_at = timezone.now()
                closeout.save()

                messages.success(request, "Event closeout has been closed. It is now read-only.")
            else:
                messages.success(request, "Attendance saved.")

            return redirect("event_closeout", pk=self.event.pk)

        if action == "add_player":
            user_id = request.POST.get("user_id")
            User = get_user_model()
            user = get_object_or_404(User, id=user_id)

            registration = (
                EventRegistration.objects
                .filter(event=self.event, user=user)
                .first()
            )

            attendance, created = EventAttendance.objects.get_or_create(
                closeout=closeout,
                user=user,
                defaults={
                    "event": self.event,
                    "registration": registration,
                    "status": EventAttendance.STATUS_ATTENDED,
                    "source": EventAttendance.SOURCE_MANUAL_ADD,
                    "is_active": True,
                    "created_by": request.user,
                    "updated_by": request.user,
                },
            )

            if not created and not attendance.is_active:
                attendance.is_active = True
                attendance.status = EventAttendance.STATUS_ATTENDED
                attendance.source = EventAttendance.SOURCE_MANUAL_ADD
                attendance.updated_by = request.user
                attendance.save()
                messages.success(request, "Player added back to closeout.")
            elif created:
                messages.success(request, "Player added to closeout.")
            else:
                messages.info(request, "Player is already in this closeout.")

            return redirect("event_closeout", pk=self.event.pk)

        if action == "remove_player":
            attendance_id = request.POST.get("attendance_id")
            attendance = get_object_or_404(
                EventAttendance,
                id=attendance_id,
                closeout=closeout,
                is_active=True,
            )

            attendance.is_active = False
            attendance.updated_by = request.user
            attendance.save()

            messages.success(request, "Player removed from closeout.")
            return redirect("event_closeout", pk=self.event.pk)

        messages.error(request, "Invalid closeout action.")
        return redirect("event_closeout", pk=self.event.pk)

class ToggleWeeklyRegistrationLimitView(AdminRequiredMixin, View):
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        settings_obj = SystemSettings.get_solo()

        settings_obj.only_allow_once_per_week_registration = (
            not settings_obj.only_allow_once_per_week_registration
        )
        settings_obj.save()

        if settings_obj.only_allow_once_per_week_registration:
            messages.success(request, "Weekly registration limit turned ON.")
        else:
            messages.success(request, "Weekly registration limit turned OFF.")

        return redirect("event_detail", pk=event.pk)