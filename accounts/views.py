from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from accounts.models import User
from registrations.models import EventRegistration

from .forms import UserRegisterForm

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

@login_required
def admin_user_profile(request, user_id):
    if not request.user.is_admin_level():
        raise PermissionDenied("You do not have access to this page.")

    profile_user = get_object_or_404(User, id=user_id)

    # 🆕 HANDLE POST (save notes)
    if request.method == "POST":
        if request.POST.get("action") == "save_admin_notes":
            profile_user.admin_notes = request.POST.get("admin_notes", "")
            profile_user.save()
            messages.success(request, "Admin notes updated successfully.")
            return redirect("admin_user_profile", user_id=profile_user.id)

    # existing logic
    current_registrations = EventRegistration.objects.filter(
        user=profile_user,
        event__start_datetime__gte=timezone.now()
    ).select_related("event").order_by("event__start_datetime")

    recent_registrations = EventRegistration.objects.filter(
        user=profile_user,
        event__start_datetime__lt=timezone.now()
    ).select_related("event").order_by("-event__start_datetime")[:5]

    # 🧠 INSIGHTS CALCULATION

    all_regs = EventRegistration.objects.filter(user=profile_user).select_related("event")

    now = timezone.now()

    past_regs = [r for r in all_regs if r.event.end_datetime and r.event.end_datetime < now]

    # --- 1. Registration Outcome ---
    total_registered = len(past_regs)
    played = len([r for r in past_regs if r.status == "playing"])
    not_played = total_registered - played

    # --- 2. Confirmed Reliability ---
    confirmed_playing = len([r for r in past_regs if r.status == "playing"])
    completed = confirmed_playing  # same logic for now
    dropped_after_confirmed = 0  # placeholder (we refine later)

    # --- 3. Waiting Conversion ---
    waiting_regs = [r for r in past_regs if r.status == "waiting"]
    waiting_total = len(waiting_regs)
    waiting_converted = 0  # placeholder (needs status logs later)

    # --- Derived Metrics ---
    completion_rate = 0
    if total_registered > 0:
        completion_rate = round((played / total_registered) * 100)

    reliability_tag = "Neutral"

    if total_registered >= 3:  # avoid small sample bias
        if completion_rate >= 80:
            reliability_tag = "Reliable Player ✅"
        elif completion_rate >= 50:
            reliability_tag = "Average Player ⚖️"
        else:
            reliability_tag = "Unreliable ❌"


    registration_delays = [
        reg.registration_delay_minutes
        for reg in all_regs
        if reg.registration_delay_minutes is not None
    ]

    avg_registration_speed = None
    fastest_registration_speed = None

    if registration_delays:
        avg_registration_speed = round(sum(registration_delays) / len(registration_delays))
        fastest_registration_speed = min(registration_delays)    


    context = {
        "profile_user": profile_user,
        "current_registrations": current_registrations,
        "recent_registrations": recent_registrations,
        "insights": {
            "total_registered": total_registered,
            "played": played,
            "not_played": not_played,
            "confirmed_playing": confirmed_playing,
            "completed": completed,
            "dropped_after_confirmed": dropped_after_confirmed,
            "waiting_total": waiting_total,
            "waiting_converted": waiting_converted,
            "completion_rate": completion_rate,
            "reliability_tag": reliability_tag,
            "avg_registration_speed": avg_registration_speed,
            "fastest_registration_speed": fastest_registration_speed,
        }
    }

    return render(request, "accounts/admin_profile.html", context)

@login_required
def profile_view(request):
    user = request.user

    # upcoming registrations
    upcoming_registrations = EventRegistration.objects.filter(
        user=user,
        event__start_datetime__gte=timezone.now()
    ).select_related("event").order_by("event__start_datetime")

    for reg in upcoming_registrations:
        reg.visible_status = get_player_visible_status(reg, reg.event)

    # recent events
    recent_events = EventRegistration.objects.filter(
        user=user,
        event__start_datetime__lt=timezone.now()
    ).select_related("event").order_by("-event__start_datetime")[:5]

    context = {
        "user": user,
        "upcoming_registrations": upcoming_registrations,
        "recent_events": recent_events,
    }

    return render(request, "accounts/profile.html", context)

def get_player_visible_status(registration, event):
    if not registration:
        return None

    if registration.status == "playing":
        return {
            "label": "Playing",
            "message": "You are in the playing list.",
            "queue_number": None,
        }

    if registration.status == "waiting":
        waiting_regs = (
            event.registrations
            .filter(status="waiting")
            .order_by("sequence_number", "id")
        )

        queue_number = 1
        for reg in waiting_regs:
            if reg.id == registration.id:
                break
            queue_number += 1

        return {
            "label": "Waiting",
            "message": "You are in the waiting list.",
            "queue_number": queue_number,
        }

    # interested and backup are both player-facing "Pending"
    return {
        "label": "Pending",
        "message": "Your status is pending.",
        "queue_number": None,
    }


class RegisterView(View):
    template_name = "accounts/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("player_home")

        form = UserRegisterForm()
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "next_url": request.GET.get("next", ""),
            },
        )

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("player_home")

        form = UserRegisterForm(request.POST)
        next_url = request.POST.get("next", "")

        if form.is_valid():
            user = form.save(commit=False)
            user.player_type = "new"
            user.email_verified = True
            user.save()

            messages.success(request, "Account created successfully. Please log in.")

            if next_url:
                return redirect(f"{reverse('login')}?next={next_url}")
            return redirect("login")

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "next_url": next_url,
            },
        )


class PlayerHomeView(View):
    template_name = "accounts/player_home.html"

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("login")

        now = timezone.now()

        upcoming_events = list(
            Event.objects
            .filter(start_datetime__gt=now, is_private=False)
            .order_by("start_datetime")
        )

        user_registrations = (
            EventRegistration.objects
            .filter(user=request.user, event__in=upcoming_events)
            .select_related("event")
        )

        registration_map = {reg.event_id: reg for reg in user_registrations}

        for event in upcoming_events:
            reg = registration_map.get(event.id)
            event.user_registration = reg
            event.player_visible_status = get_player_visible_status(reg, event)

        return render(
            request,
            self.template_name,
            {
                "events": upcoming_events,
                "now": now,
            },
        )


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)
            return redirect(self._redirect_user(request.user))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        next_url = self.get_redirect_url()
        if next_url:
            return next_url
        return reverse(self._redirect_user(self.request.user))

    def _redirect_user(self, user):
        if user.is_superuser or user.is_staff:
            return "event_list"
        return "player_home"
    


