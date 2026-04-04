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


@login_required
def join_event(request, token):
    event = get_object_or_404(Event, registration_token=token)

    if timezone.now() >= event.start_datetime:
        return render(request, "registrations/join_closed.html", {"event": event})

    if request.method == "POST":
        registration, created = register_user_for_event(
            event,
            request.user,
            changed_by=request.user,
        )

        if created:
            messages.success(request, f"You joined as {registration.status}.")
        else:
            messages.info(request, f"You are already registered as {registration.status}.")

        return render(
            request,
            "registrations/join_success.html",
            {
                "event": event,
                "registration": registration,
                "created": created,
            },
        )

    return render(request, "registrations/join_page.html", {"event": event})