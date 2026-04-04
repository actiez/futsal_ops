from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from registrations.models import EventRegistration

from .forms import UserRegisterForm


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
            Event.objects.filter(start_datetime__gt=now).order_by("start_datetime")
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