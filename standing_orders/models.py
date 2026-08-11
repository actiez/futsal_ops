from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class StandingOrder(models.Model):
    ACTION_CREATE_EVENT = "create_event"
    ACTION_SET_WEEKLY_LIMIT = "set_weekly_limit"

    ACTION_CHOICES = [
        (ACTION_CREATE_EVENT, "Create Event"),
        (ACTION_SET_WEEKLY_LIMIT, "Set Weekly Limit"),
    ]

    FREQUENCY_WEEKLY = "weekly"

    FREQUENCY_CHOICES = [
        (FREQUENCY_WEEKLY, "Weekly"),
    ]

    DAY_MONDAY = 0
    DAY_TUESDAY = 1
    DAY_WEDNESDAY = 2
    DAY_THURSDAY = 3
    DAY_FRIDAY = 4
    DAY_SATURDAY = 5
    DAY_SUNDAY = 6

    DAY_CHOICES = [
        (DAY_MONDAY, "Monday"),
        (DAY_TUESDAY, "Tuesday"),
        (DAY_WEDNESDAY, "Wednesday"),
        (DAY_THURSDAY, "Thursday"),
        (DAY_FRIDAY, "Friday"),
        (DAY_SATURDAY, "Saturday"),
        (DAY_SUNDAY, "Sunday"),
    ]

    LEAVE_CUTOFF_CHOICES = [
        (None, "No cutoff"),
        (30, "30 minutes before"),
        (60, "60 minutes before"),
        (90, "90 minutes before"),
        (120, "120 minutes before"),
        (150, "150 minutes before"),
        (180, "180 minutes before"),
    ]

    name = models.CharField(max_length=120)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default=FREQUENCY_WEEKLY,
    )

    run_day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    run_time = models.TimeField()

    is_active = models.BooleanField(default=True)

    # For create_event action
    event_day_of_week = models.PositiveSmallIntegerField(
        choices=DAY_CHOICES,
        null=True,
        blank=True,
    )
    event_start_time = models.TimeField(null=True, blank=True)
    event_end_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    amount_payable = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    playing_slots = models.PositiveIntegerField(null=True, blank=True)
    waiting_slots = models.PositiveIntegerField(null=True, blank=True)
    backup_slots = models.PositiveIntegerField(null=True, blank=True)
    is_private = models.BooleanField(default=False)

    leave_cutoff_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=LEAVE_CUTOFF_CHOICES,
        help_text="Events created by this standing order will lock self-leaving after this cutoff before kick-off.",
    )

    # For weekly limit action
    weekly_limit_enabled = models.BooleanField(null=True, blank=True)

    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_standing_orders",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["run_day_of_week", "run_time", "name"]

    def __str__(self):
        return self.name

    @property
    def action_label(self):
        return dict(self.ACTION_CHOICES).get(self.action, self.action)

    @property
    def run_day_label(self):
        return dict(self.DAY_CHOICES).get(self.run_day_of_week, self.run_day_of_week)

    @property
    def event_day_label(self):
        if self.event_day_of_week is None:
            return ""
        return dict(self.DAY_CHOICES).get(self.event_day_of_week, self.event_day_of_week)

    @property
    def leave_cutoff_label(self):
        if not self.leave_cutoff_minutes:
            return "No cutoff"
        return dict(self.LEAVE_CUTOFF_CHOICES).get(
            self.leave_cutoff_minutes,
            f"{self.leave_cutoff_minutes} minutes before",
        )

    def calculate_next_run_at(self, from_datetime=None):
        from_datetime = from_datetime or timezone.now()
        local_from = timezone.localtime(from_datetime)

        days_ahead = self.run_day_of_week - local_from.weekday()

        candidate_date = local_from.date() + timedelta(days=days_ahead)
        candidate_datetime = timezone.make_aware(
            timezone.datetime.combine(candidate_date, self.run_time),
            timezone.get_current_timezone(),
        )

        if candidate_datetime <= local_from:
            candidate_datetime += timedelta(days=7)

        return candidate_datetime


class StandingOrderRunLog(models.Model):
    STATUS_SUCCESS = "success"
    STATUS_SKIPPED = "skipped"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Success"),
        (STATUS_SKIPPED, "Skipped"),
        (STATUS_FAILED, "Failed"),
    ]

    standing_order = models.ForeignKey(
        StandingOrder,
        on_delete=models.CASCADE,
        related_name="run_logs",
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message = models.TextField(blank=True)

    created_event = models.ForeignKey(
        "events.Event",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="standing_order_run_logs",
    )

    ran_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ran_at"]

    def __str__(self):
        return f"{self.standing_order.name} - {self.status}"