from registrations.models import EventRegistration, EventStatusLog


def get_next_sequence_number(event):
    last_registration = (
        EventRegistration.objects.filter(event=event)
        .order_by("-sequence_number")
        .first()
    )

    return 1 if not last_registration else last_registration.sequence_number + 1


def get_next_waiting_sequence_number(event):
    last_waiting = (
        EventRegistration.objects
        .filter(event=event, status=EventRegistration.STATUS_WAITING)
        .order_by("-sequence_number", "-id")
        .first()
    )

    if last_waiting:
        return last_waiting.sequence_number + 1

    return get_next_sequence_number(event)


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
    if user.player_type == user.PLAYER_NAUGHTY:
        return EventRegistration.STATUS_BACKUP

    if user.player_type == user.PLAYER_CORE:
        if has_playing_slot_available(event):
            return EventRegistration.STATUS_PLAYING

        if has_waiting_slot_available(event):
            return EventRegistration.STATUS_WAITING

        return EventRegistration.STATUS_INTERESTED

    return EventRegistration.STATUS_INTERESTED


def register_user_for_event(event, user, changed_by=None):
    existing = EventRegistration.objects.filter(event=event, user=user).first()

    if existing and existing.status != EventRegistration.STATUS_REMOVED:
        return existing, False

    default_status = get_default_status_for_user(event, user)

    if existing and existing.status == EventRegistration.STATUS_REMOVED:
        old_status = existing.status
        existing.status = default_status
        existing.sequence_number = get_next_sequence_number(event)

        if default_status == EventRegistration.STATUS_WAITING:
            existing.sequence_number = get_next_waiting_sequence_number(event)

        existing.save()

        EventStatusLog.objects.create(
            registration=existing,
            old_status=old_status,
            new_status=default_status,
            changed_by=changed_by,
        )

        return existing, True

    sequence_number = get_next_sequence_number(event)

    if default_status == EventRegistration.STATUS_WAITING:
        sequence_number = get_next_waiting_sequence_number(event)

    registration = EventRegistration.objects.create(
        event=event,
        user=user,
        sequence_number=sequence_number,
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
            .order_by("sequence_number", "id")
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


def rebalance_event_slots(event, changed_by=None):
    """
    Conservative rebalance rule:

    - Waiting players can auto-promote to Playing when a Playing slot opens.
    - Interested players must NOT auto-move to Waiting or Playing.
    - Regular/New players stay Interested unless admin manually moves them.
    - Core players are handled automatically only when they join/rejoin.
    - Naughty players stay Backup unless admin manually changes them.
    """
    auto_promote_waiting(event, changed_by=changed_by)


def update_registration_status(registration, new_status, changed_by=None):
    old_status = registration.status

    if old_status == new_status:
        return registration, "no_change"

    registration.status = new_status

    if (
        new_status == EventRegistration.STATUS_WAITING
        and old_status != EventRegistration.STATUS_WAITING
    ):
        registration.sequence_number = get_next_waiting_sequence_number(registration.event)

    registration.save()

    EventStatusLog.objects.create(
        registration=registration,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
    )

    return registration, "updated"


def remove_registration(registration, changed_by=None):
    old_status = registration.status

    if old_status == EventRegistration.STATUS_REMOVED:
        return registration, "no_change"

    registration.status = EventRegistration.STATUS_REMOVED
    registration.save()

    EventStatusLog.objects.create(
        registration=registration,
        old_status=old_status,
        new_status=EventRegistration.STATUS_REMOVED,
        changed_by=changed_by,
    )

    return registration, "removed"