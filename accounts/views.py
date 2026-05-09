from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from events.models import Event, EventAttendance, EventCloseout
from accounts.models import User
from registrations.models import EventRegistration

from .forms import UserRegisterForm, UserProfileUpdateForm


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
    current_registrations = (
        EventRegistration.objects
        .filter(
            user=profile_user,
            event__start_datetime__gte=timezone.now()
        )
        .exclude(status=EventRegistration.STATUS_REMOVED)
        .select_related("event")
        .order_by("event__start_datetime")
    )

    recent_registrations = EventRegistration.objects.filter(
        user=profile_user,
        event__start_datetime__lt=timezone.now()
    ).select_related("event").order_by("-event__start_datetime")[:5]

    # 🧠 INSIGHTS CALCULATION
    # Closeout is the new source of truth.
    # Fallback to old registration logic only if this player has no closeout data yet.

    closed_closeout_statuses = [
        EventCloseout.STATUS_CLOSED_MANUAL,
        EventCloseout.STATUS_CLOSED_AUTO,
    ]

    attendance_records = (
        EventAttendance.objects
        .filter(
            user=profile_user,
            is_active=True,
            closeout__status__in=closed_closeout_statuses,
        )
        .select_related("event", "closeout")
    )

    closeout_total = attendance_records.count()
    attended = attendance_records.filter(status=EventAttendance.STATUS_ATTENDED).count()
    absent = attendance_records.filter(status=EventAttendance.STATUS_ABSENT).count()
    excused = attendance_records.filter(status=EventAttendance.STATUS_EXCUSED).count()

    # Excused should not punish reliability.
    reliability_base = attended + absent

    attendance_rate = 0
    if reliability_base > 0:
        attendance_rate = round((attended / reliability_base) * 100)

    no_show_rate = 0
    if reliability_base > 0:
        no_show_rate = round((absent / reliability_base) * 100)

    reliability_tag = "New Sample"

    if reliability_base >= 3:
        if attendance_rate >= 85:
            reliability_tag = "Reliable Player ✅"
        elif attendance_rate >= 60:
            reliability_tag = "Average Player ⚖️"
        else:
            reliability_tag = "Watchlist ⚠️"

    # Fallback for old data before closeout existed
    if closeout_total == 0:
        all_regs = EventRegistration.objects.filter(user=profile_user).select_related("event")

        now = timezone.now()
        past_regs = [
            r for r in all_regs
            if r.event.end_datetime and r.event.end_datetime < now
        ]

        closeout_total = len(past_regs)
        attended = len([r for r in past_regs if r.status == EventRegistration.STATUS_PLAYING])
        absent = closeout_total - attended
        excused = 0

        reliability_base = attended + absent

        attendance_rate = 0
        if reliability_base > 0:
            attendance_rate = round((attended / reliability_base) * 100)

        no_show_rate = 0
        if reliability_base > 0:
            no_show_rate = round((absent / reliability_base) * 100)

        reliability_tag = "Legacy Data"

        if reliability_base >= 3:
            if attendance_rate >= 85:
                reliability_tag = "Reliable Player ✅"
            elif attendance_rate >= 60:
                reliability_tag = "Average Player ⚖️"
            else:
                reliability_tag = "Watchlist ⚠️"

    registration_delays = [
        reg.registration_delay_minutes
        for reg in EventRegistration.objects.filter(user=profile_user).select_related("event")
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
            "closeout_total": closeout_total,
            "attended": attended,
            "absent": absent,
            "excused": excused,
            "attendance_rate": attendance_rate,
            "no_show_rate": no_show_rate,
            "reliability_base": reliability_base,
            "reliability_tag": reliability_tag,
            "avg_registration_speed": avg_registration_speed,
            "fastest_registration_speed": fastest_registration_speed,

            # Backward-compatible keys for existing template sections
            "total_registered": closeout_total,
            "played": attended,
            "not_played": absent,
            "confirmed_playing": reliability_base,
            "completed": attended,
            "dropped_after_confirmed": absent,
            "waiting_total": 0,
            "waiting_converted": 0,
            "completion_rate": attendance_rate,
        }
    }

    return render(request, "accounts/admin_profile.html", context)

@login_required
def profile_view(request):
    user = request.user

    closed_closeout_statuses = [
        EventCloseout.STATUS_CLOSED_MANUAL,
        EventCloseout.STATUS_CLOSED_AUTO,
    ]

    attendance_records = (
        EventAttendance.objects
        .filter(
            user=user,
            is_active=True,
            closeout__status__in=closed_closeout_statuses,
        )
    )

    attended_count = attendance_records.filter(
        status=EventAttendance.STATUS_ATTENDED
    ).count()

    absent_count = attendance_records.filter(
        status=EventAttendance.STATUS_ABSENT
    ).count()

    excused_count = attendance_records.filter(
        status=EventAttendance.STATUS_EXCUSED
    ).count()

    attendance_base = attended_count + absent_count

    attendance_rate = 0
    if attendance_base > 0:
        attendance_rate = round((attended_count / attendance_base) * 100)

    # upcoming registrations
    upcoming_registrations = (
        EventRegistration.objects
        .filter(
            user=user,
            event__start_datetime__gte=timezone.now()
        )
        .exclude(status=EventRegistration.STATUS_REMOVED)
        .select_related("event")
        .order_by("event__start_datetime")
    )

    for reg in upcoming_registrations:
        reg.visible_status = get_player_visible_status(reg, reg.event)

    # recent events
    recent_events = (
        EventRegistration.objects
        .filter(
            user=user,
            event__start_datetime__lt=timezone.now()
        )
        .exclude(status=EventRegistration.STATUS_REMOVED)
        .select_related("event")
        .order_by("-event__start_datetime")[:5]
    )

    context = {
        "user": user,
        "upcoming_registrations": upcoming_registrations,
        "recent_events": recent_events,
        "attended_count": attended_count,
        "absent_count": absent_count,
        "excused_count": excused_count,
        "attendance_rate": attendance_rate,
    }

    return render(request, "accounts/profile.html", context)

@login_required
def profile_edit_view(request):
    if request.method == "POST":
        form = UserProfileUpdateForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        form = UserProfileUpdateForm(instance=request.user)

    return render(
        request,
        "accounts/profile_edit.html",
        {
            "form": form,
        },
    )

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
            .exclude(status=EventRegistration.STATUS_REMOVED)
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
    
@login_required
def user_list_view(request):
    if not request.user.is_admin_level():
        raise PermissionDenied("You do not have access to this page.")

    search_query = request.GET.get("q", "").strip()

    users = User.objects.all().order_by("first_name", "last_name", "username")

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(mobile_number__icontains=search_query)
        )

    return render(
        request,
        "accounts/user_list.html",
        {
            "users": users,
            "search_query": search_query,
        },
    )

@login_required
def generate_password_reset_link(request, user_id):
    if not request.user.is_superadmin_level():
        raise PermissionDenied("Only superadmin can generate password reset links.")

    target_user = get_object_or_404(User, id=user_id)

    uid = urlsafe_base64_encode(force_bytes(target_user.pk))
    token = default_token_generator.make_token(target_user)

    reset_url = request.build_absolute_uri(
        reverse(
            "password_reset_confirm",
            kwargs={
                "uidb64": uid,
                "token": token,
            },
        )
    )

    return render(
        request,
        "accounts/generated_password_reset_link.html",
        {
            "target_user": target_user,
            "reset_url": reset_url,
        },
    )