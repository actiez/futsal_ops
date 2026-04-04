from django.conf import settings
from django.db import models
from django.utils import timezone

import uuid

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

    title = models.CharField(max_length=255)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    location = models.CharField(max_length=255)
    amount_payable = models.DecimalField(max_digits=8, decimal_places=2)

    playing_slots = models.PositiveIntegerField(default=15)
    waiting_slots = models.PositiveIntegerField(default=5)
    backup_slots = models.PositiveIntegerField(default=3)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)

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
        return self.start_datetime.strftime("%A")

    @property
    def date_display(self):
        return self.start_datetime.strftime("%d %B %Y")

    @property
    def time_range_display(self):
        start = self.start_datetime.strftime("%I:%M %p").lstrip("0")
        end = self.end_datetime.strftime("%I:%M %p").lstrip("0")
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