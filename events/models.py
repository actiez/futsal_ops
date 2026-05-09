from django.conf import settings
from django.db import models
from django.utils import timezone

import uuid
import secrets
import string

def generate_event_code():
    alphabet = string.ascii_uppercase + string.digits
    return "EVT-" + "".join(secrets.choice(alphabet) for _ in range(6))

class Event(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_OPEN = "open"
    STATUS_FINALIZED = "finalized"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_OPEN, "Open"),
        (STATUS_FINALIZED, "Finalized"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    registration_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    event_code = models.CharField(
        max_length=20,
        unique=True,
        default=generate_event_code,
        editable=False,
    )

    title = models.CharField(max_length=255)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    location = models.CharField(max_length=255)
    amount_payable = models.DecimalField(max_digits=8, decimal_places=2)

    playing_slots = models.PositiveIntegerField(default=15)
    waiting_slots = models.PositiveIntegerField(default=5)
    backup_slots = models.PositiveIntegerField(default=3)

    is_private = models.BooleanField(
        default=False,
        help_text="Private events are hidden from the public event list but accessible by registration link.",
    )
   
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_events",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_datetime"]

    def __str__(self):
        return self.title

    @property
    def is_upcoming(self):
        return self.start_datetime > timezone.now()

    @property
    def weekday_display(self):
        local_start = timezone.localtime(self.start_datetime)
        return local_start.strftime("%A")

    @property
    def date_display(self):
        local_start = timezone.localtime(self.start_datetime)
        return local_start.strftime("%d %B %Y")

    @property
    def time_range_display(self):
        local_start = timezone.localtime(self.start_datetime)
        local_end = timezone.localtime(self.end_datetime)
        start = local_start.strftime("%I:%M %p").lstrip("0")
        end = local_end.strftime("%I:%M %p").lstrip("0")
        return f"{start} to {end}"

    @property
    def effective_status(self):
        from registrations.models import EventRegistration

        now = timezone.now()

        if now >= self.end_datetime:
            return "completed"

        playing_count = self.registrations.filter(
            status=EventRegistration.STATUS_PLAYING
        ).count()

        waiting_count = self.registrations.filter(
            status=EventRegistration.STATUS_WAITING
        ).count()

        if playing_count >= self.playing_slots and waiting_count >= self.waiting_slots:
            return "full"

        if playing_count >= self.playing_slots:
            return "playing_full"

        return "open"

    @property
    def effective_status_label(self):
        labels = {
            "open": "Open",
            "playing_full": "Playing Full",
            "full": "Full",
            "completed": "Completed",
        }
        return labels.get(self.effective_status, self.effective_status)
    
class EventCloseout(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CLOSED_MANUAL = "closed_manual"
    STATUS_CLOSED_AUTO = "closed_auto"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CLOSED_MANUAL, "Closed Manually"),
        (STATUS_CLOSED_AUTO, "Closed Automatically"),
    ]

    event = models.OneToOneField(
        Event,
        on_delete=models.CASCADE,
        related_name="closeout",
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_event_closeouts",
    )

    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="closed_event_closeouts",
    )

    closed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_closed(self):
        return self.status in {
            self.STATUS_CLOSED_MANUAL,
            self.STATUS_CLOSED_AUTO,
        }

    def __str__(self):
        return f"{self.event} - {self.status}"


class EventAttendance(models.Model):
    STATUS_ATTENDED = "attended"
    STATUS_ABSENT = "absent"
    STATUS_EXCUSED = "excused"

    STATUS_CHOICES = [
        (STATUS_ATTENDED, "Attended"),
        (STATUS_ABSENT, "Absent"),
        (STATUS_EXCUSED, "Excused"),
    ]

    SOURCE_SNAPSHOT = "snapshot"
    SOURCE_MANUAL_ADD = "manual_add"
    SOURCE_AUTO_CLOSE = "auto_close"

    SOURCE_CHOICES = [
        (SOURCE_SNAPSHOT, "Snapshot"),
        (SOURCE_MANUAL_ADD, "Manual Add"),
        (SOURCE_AUTO_CLOSE, "Auto Close"),
    ]

    closeout = models.ForeignKey(
        EventCloseout,
        on_delete=models.CASCADE,
        related_name="attendances",
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="attendances",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_attendances",
    )

    registration = models.ForeignKey(
        "registrations.EventRegistration",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_records",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ATTENDED,
    )

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_SNAPSHOT,
    )

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_event_attendances",
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_event_attendances",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("closeout", "user")
        ordering = ["user__first_name", "user__last_name", "user__username"]

    def __str__(self):
        return f"{self.event} - {self.user} - {self.status}"