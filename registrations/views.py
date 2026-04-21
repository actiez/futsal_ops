from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from accounts.models import User
from core.mixins import AdminRequiredMixin
from django.db.models import Q
from events.models import Event

from django.http import HttpResponse

from .forms import EventRegistrationAdminForm
from .models import EventRegistration
from .services import (
    register_user_for_event,
    update_registration_status,
    rebalance_event_slots,
)


class EventRegistrationCreateView(AdminRequiredMixin, View):
    template_name = "registrations/add.html"

    def get_filtered_users(self, event, search_query):
        registered_user_ids = event.registrations.values_list("user_id", flat=True)

        users = User.objects.exclude(id__in=registered_user_ids)

        if search_query:
            users = users.filter(
                Q(username__icontains=search_query)
                | Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
                | Q(email__icontains=search_query)
            )

        return users.order_by("first_name", "last_name", "username")

    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        search_query = request.GET.get("q", "").strip()

        form = EventRegistrationAdminForm()
        form.fields["user"].queryset = self.get_filtered_users(event, search_query)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "event": event,
                "search_query": search_query,
            },
        )

    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        search_query = request.GET.get("q", "").strip()

        form = EventRegistrationAdminForm(request.POST)
        form.fields["user"].queryset = self.get_filtered_users(event, search_query)

        if form.is_valid():
            user = form.cleaned_data["user"]
            registration, created = register_user_for_event(
                event,
                user,
                changed_by=request.user,
            )

            if created:
                messages.success(
                    request,
                    f"{user.username} added to event as {registration.status}."
                )
            else:
                messages.warning(
                    request,
                    f"{user.username} is already registered for this event."
                )

            return redirect("event_detail", pk=event.pk)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "event": event,
                "search_query": search_query,
            },
        )


class RegistrationStatusUpdateView(AdminRequiredMixin, View):
    def post(self, request, pk, status):
        registration = get_object_or_404(EventRegistration, pk=pk)

        registration, result = update_registration_status(
            registration,
            status,
            changed_by=request.user,
        )

        if result == "updated":
            messages.success(
                request,
                f"{registration.user.username} moved to {registration.status}."
            )

        return redirect("event_detail", pk=registration.event.pk)


class RegistrationDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        registration = get_object_or_404(EventRegistration, pk=pk)
        event = registration.event

        registration.delete()

        messages.success(request, "Player removed from event.")

        rebalance_event_slots(event, changed_by=request.user)

        return redirect("event_detail", pk=event.pk)


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

    return {
        "label": "Pending",
        "message": "Your status is pending.",
        "queue_number": None,
    }


@login_required
def join_event(request, token):
    event = get_object_or_404(Event, registration_token=token)

    if timezone.now() >= event.start_datetime:
        return render(request, "registrations/join_closed.html", {"event": event})

    existing_registration = (
        EventRegistration.objects
        .filter(event=event, user=request.user)
        .first()
    )

    visible_status = get_player_visible_status(existing_registration, event)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "join":
            if existing_registration:
                messages.info(request, "You are already registered for this event.")
                return redirect("join_event", token=event.registration_token)

            registration, created = register_user_for_event(
                event,
                request.user,
                changed_by=request.user,
            )

            visible_status = get_player_visible_status(registration, event)

            if visible_status["label"] == "Playing":
                messages.success(request, "You are in the playing list.")
            elif visible_status["label"] == "Waiting":
                messages.success(
                    request,
                    f"You are in the waiting list. You are currently #{visible_status['queue_number']} in the waiting list.",
                )
            else:
                messages.success(
                    request,
                    "Your status is pending. Pending means you may move into the waiting list when a slot opens, subject to queue.",
                )

            return redirect("join_event", token=event.registration_token)

        if action == "leave_warn":
            if not existing_registration:
                messages.warning(request, "You are not registered for this event.")
                return redirect("join_event", token=event.registration_token)

            return render(
                request,
                "registrations/join_page.html",
                {
                    "event": event,
                    "existing_registration": existing_registration,
                    "visible_status": visible_status,
                    "leave_stage": "warn",
                },
            )

        if action == "leave_confirm":
            if not existing_registration:
                messages.warning(request, "You are not registered for this event.")
                return redirect("join_event", token=event.registration_token)

            existing_registration.delete()
            rebalance_event_slots(event, changed_by=request.user)

            messages.success(
                request,
                "You have left the game. If you join again later, you will need to queue again.",
            )
            return redirect("join_event", token=event.registration_token)

    return render(
        request,
        "registrations/join_page.html",
        {
            "event": event,
            "existing_registration": existing_registration,
            "visible_status": visible_status,
            "leave_stage": None,
        },
    )