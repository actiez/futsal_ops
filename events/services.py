from django.db import transaction
from django.utils import timezone

from .models import Event, EventCloseout, EventAttendance
from registrations.models import EventRegistration


def event_is_closeout_eligible(event):
    if event.status == Event.STATUS_CANCELLED:
        return False

    return event.end_datetime <= timezone.now()


@transaction.atomic
def create_closeout_snapshot(event, created_by=None):
    closeout, created = EventCloseout.objects.get_or_create(
        event=event,
        defaults={
            "status": EventCloseout.STATUS_PENDING,
            "created_by": created_by,
        },
    )

    if not created:
        return closeout

    playing_regs = (
        EventRegistration.objects
        .filter(event=event, status=EventRegistration.STATUS_PLAYING)
        .select_related("user")
        .order_by("sequence_number", "id")
    )

    for reg in playing_regs:
        EventAttendance.objects.get_or_create(
            closeout=closeout,
            user=reg.user,
            defaults={
                "event": event,
                "registration": reg,
                "status": EventAttendance.STATUS_ATTENDED,
                "source": EventAttendance.SOURCE_SNAPSHOT,
                "is_active": True,
                "created_by": created_by,
                "updated_by": created_by,
            },
        )

    return closeout


@transaction.atomic
def auto_close_event(event):
    if EventCloseout.objects.filter(event=event).exists():
        return None

    closeout = EventCloseout.objects.create(
        event=event,
        status=EventCloseout.STATUS_CLOSED_AUTO,
        closed_at=timezone.now(),
    )

    playing_regs = (
        EventRegistration.objects
        .filter(event=event, status=EventRegistration.STATUS_PLAYING)
        .select_related("user")
        .order_by("sequence_number", "id")
    )

    for reg in playing_regs:
        EventAttendance.objects.create(
            closeout=closeout,
            event=event,
            user=reg.user,
            registration=reg,
            status=EventAttendance.STATUS_ATTENDED,
            source=EventAttendance.SOURCE_AUTO_CLOSE,
            is_active=True,
        )

    return closeout