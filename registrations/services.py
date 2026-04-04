from registrations.models import EventRegistration, EventStatusLog


def get_next_sequence_number(event):
    last_registration = (
        EventRegistration.objects.filter(event=event)
        .order_by("-sequence_number")
        .first()
    )
    return 1 if not last_registration else last_registration.sequence_number + 1


def has_playing_slot_available(event):
    playing_count = EventRegistration.objects.filter(
        event=event,
        status=EventRegistration.STATUS_PLAYING,
    ).count()
    return playing_count < event.playing_slots


def has_waiting_slot_available(event):
    waiting_count = EventRegistration.objects.filter(
        event=event,
        status=EventRegistration.STATUS_WAITING,
    ).count()
    return waiting_count < event.waiting_slots


def get_default_status_for_user(event, user):
    if user.player_type == user.PLAYER_CORE:
        if has_playing_slot_available(event):
            return EventRegistration.STATUS_PLAYING
        if has_waiting_slot_available(event):
            return EventRegistration.STATUS_WAITING
        return EventRegistration.STATUS_INTERESTED

    if user.player_type == user.PLAYER_NAUGHTY:
        return EventRegistration.STATUS_BACKUP

    return EventRegistration.STATUS_INTERESTED


def register_user_for_event(event, user, changed_by=None):
    existing = EventRegistration.objects.filter(event=event, user=user).first()
    if existing:
        return existing, False

    default_status = get_default_status_for_user(event, user)

    registration = EventRegistration.objects.create(
        event=event,
        user=user,
        sequence_number=get_next_sequence_number(event),
        status=default_status,
    )

    EventStatusLog.objects.create(
        registration=registration,
        old_status="",
        new_status=default_status,
        changed_by=changed_by,
    )

    return registration, True


def auto_promote_waiting(event, changed_by=None):
    while has_playing_slot_available(event):
        next_waiting = (
            EventRegistration.objects
            .filter(event=event, status=EventRegistration.STATUS_WAITING)
            .order_by("sequence_number")
            .first()
        )

        if not next_waiting:
            break

        old_status = next_waiting.status
        next_waiting.status = EventRegistration.STATUS_PLAYING
        next_waiting.save()

        EventStatusLog.objects.create(
            registration=next_waiting,
            old_status=old_status,
            new_status=EventRegistration.STATUS_PLAYING,
            changed_by=changed_by,
        )


def auto_fill_waiting_from_interested(event, changed_by=None):
    while has_waiting_slot_available(event):
        next_interested = (
            EventRegistration.objects
            .filter(
                event=event,
                status=EventRegistration.STATUS_INTERESTED,
                user__player_type="core",
            )
            .order_by("sequence_number")
            .first()
        )

        if not next_interested:
            next_interested = (
                EventRegistration.objects
                .filter(
                    event=event,
                    status=EventRegistration.STATUS_INTERESTED,
                    user__player_type__in=["regular", "new"],
                )
                .order_by("sequence_number")
                .first()
            )

        if not next_interested:
            break

        old_status = next_interested.status
        next_interested.status = EventRegistration.STATUS_WAITING
        next_interested.save()

        EventStatusLog.objects.create(
            registration=next_interested,
            old_status=old_status,
            new_status=EventRegistration.STATUS_WAITING,
            changed_by=changed_by,
        )


def rebalance_event_slots(event, changed_by=None):
    auto_promote_waiting(event, changed_by=changed_by)
    auto_fill_waiting_from_interested(event, changed_by=changed_by)


def update_registration_status(registration, new_status, changed_by=None):
    old_status = registration.status

    if old_status == new_status:
        return registration, "no_change"

    registration.status = new_status
    registration.save()

    EventStatusLog.objects.create(
        registration=registration,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
    )

    return registration, "updated"