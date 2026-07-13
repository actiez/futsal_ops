from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from events.models import Event
from system_settings.models import SystemSettings

from .models import StandingOrder, StandingOrderRunLog


def get_next_date_for_weekday(base_date, target_weekday):
    """
    Returns the next date matching target_weekday from base_date.
    Monday = 0, Sunday = 6.
    If base_date itself matches, it returns base_date.
    """
    days_ahead = target_weekday - base_date.weekday()

    if days_ahead < 0:
        days_ahead += 7

    return base_date + timedelta(days=days_ahead)


def build_event_datetimes(standing_order, from_datetime=None):
    from_datetime = from_datetime or timezone.now()
    local_from = timezone.localtime(from_datetime)

    event_date = get_next_date_for_weekday(
        local_from.date(),
        standing_order.event_day_of_week,
    )

    start_datetime = timezone.make_aware(
        timezone.datetime.combine(event_date, standing_order.event_start_time),
        timezone.get_current_timezone(),
    )

    end_datetime = timezone.make_aware(
        timezone.datetime.combine(event_date, standing_order.event_end_time),
        timezone.get_current_timezone(),
    )

    if end_datetime <= start_datetime:
        end_datetime += timedelta(days=1)

    return start_datetime, end_datetime


def validate_standing_order_for_run(standing_order):
    if not standing_order.is_active:
        return False, "Standing order is paused."

    if standing_order.action == StandingOrder.ACTION_CREATE_EVENT:
        required_fields = [
            standing_order.event_day_of_week,
            standing_order.event_start_time,
            standing_order.event_end_time,
            standing_order.location,
            standing_order.amount_payable,
            standing_order.playing_slots,
            standing_order.waiting_slots,
            standing_order.backup_slots,
        ]

        if any(value in [None, ""] for value in required_fields):
            return False, "Create event standing order has incomplete event details."

    if standing_order.action == StandingOrder.ACTION_SET_WEEKLY_LIMIT:
        if standing_order.weekly_limit_enabled is None:
            return False, "Weekly limit standing order has no target value."

    return True, ""


@transaction.atomic
def run_create_event_order(standing_order):
    start_datetime, end_datetime = build_event_datetimes(standing_order)

    duplicate_event = Event.objects.filter(
        start_datetime=start_datetime,
        location=standing_order.location,
    ).first()

    if duplicate_event:
        return StandingOrderRunLog.objects.create(
            standing_order=standing_order,
            status=StandingOrderRunLog.STATUS_SKIPPED,
            message=f"Skipped. Event already exists: {duplicate_event.event_code}",
            created_event=duplicate_event,
        )

    event = Event.objects.create(
        title=standing_order.name,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        location=standing_order.location,
        amount_payable=standing_order.amount_payable,
        playing_slots=standing_order.playing_slots,
        waiting_slots=standing_order.waiting_slots,
        backup_slots=standing_order.backup_slots,
        is_private=standing_order.is_private,
        created_by=standing_order.created_by,
    )

    return StandingOrderRunLog.objects.create(
        standing_order=standing_order,
        status=StandingOrderRunLog.STATUS_SUCCESS,
        message=f"Created event: {event.event_code}",
        created_event=event,
    )


@transaction.atomic
def run_weekly_limit_order(standing_order):
    settings_obj = SystemSettings.get_solo()
    settings_obj.only_allow_once_per_week_registration = standing_order.weekly_limit_enabled
    settings_obj.save()

    state = "ON" if standing_order.weekly_limit_enabled else "OFF"

    return StandingOrderRunLog.objects.create(
        standing_order=standing_order,
        status=StandingOrderRunLog.STATUS_SUCCESS,
        message=f"Weekly registration limit set to {state}.",
    )


@transaction.atomic
def run_standing_order(standing_order):
    is_valid, error_message = validate_standing_order_for_run(standing_order)

    if not is_valid:
        log = StandingOrderRunLog.objects.create(
            standing_order=standing_order,
            status=StandingOrderRunLog.STATUS_FAILED,
            message=error_message,
        )
    else:
        try:
            if standing_order.action == StandingOrder.ACTION_CREATE_EVENT:
                log = run_create_event_order(standing_order)
            elif standing_order.action == StandingOrder.ACTION_SET_WEEKLY_LIMIT:
                log = run_weekly_limit_order(standing_order)
            else:
                log = StandingOrderRunLog.objects.create(
                    standing_order=standing_order,
                    status=StandingOrderRunLog.STATUS_FAILED,
                    message="Unknown standing order action.",
                )
        except Exception as error:
            log = StandingOrderRunLog.objects.create(
                standing_order=standing_order,
                status=StandingOrderRunLog.STATUS_FAILED,
                message=str(error),
            )

    standing_order.last_run_at = timezone.now()
    standing_order.next_run_at = standing_order.calculate_next_run_at()
    standing_order.save(update_fields=["last_run_at", "next_run_at", "updated_at"])

    return log


def run_due_standing_orders():
    now = timezone.now()

    due_orders = StandingOrder.objects.filter(
        is_active=True,
        next_run_at__lte=now,
    ).order_by("next_run_at", "id")

    logs = []

    for standing_order in due_orders:
        logs.append(run_standing_order(standing_order))

    return logs


def refresh_next_run_at(standing_order):
    standing_order.next_run_at = standing_order.calculate_next_run_at()
    standing_order.save(update_fields=["next_run_at", "updated_at"])
    return standing_order