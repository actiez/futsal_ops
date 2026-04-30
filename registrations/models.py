from django.conf import settings
from django.db import models
from events.models import Event


class EventRegistration(models.Model):
    STATUS_INTERESTED = "interested"
    STATUS_PLAYING = "playing"
    STATUS_WAITING = "waiting"
    STATUS_BACKUP = "backup"
    STATUS_REMOVED = "removed"

    STATUS_CHOICES = [
        (STATUS_INTERESTED, "Interested"),
        (STATUS_PLAYING, "Playing"),
        (STATUS_WAITING, "Waiting"),
        (STATUS_BACKUP, "Backup"),
        (STATUS_REMOVED, "Removed"),
    ]

    SOURCE_WEB = "web"
    SOURCE_WHATSAPP = "whatsapp"
    SOURCE_ADMIN = "admin"

    SOURCE_CHOICES = [
        (SOURCE_WEB, "Web"),
        (SOURCE_WHATSAPP, "WhatsApp"),
        (SOURCE_ADMIN, "Admin"),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_registrations")

    sequence_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INTERESTED)

    source = models.CharField(
    max_length=20,
    choices=SOURCE_CHOICES,
    default=SOURCE_WEB,
    )

    registered_at = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    @property
    def registration_delay_seconds(self):
        if self.event and self.event.created_at and self.registered_at:
            return int((self.registered_at - self.event.created_at).total_seconds())
        return None

    @property
    def registration_delay_minutes(self):
        seconds = self.registration_delay_seconds
        if seconds is None:
            return None
        return round(seconds / 60)

    class Meta:
        unique_together = ("event", "user")
        ordering = ["sequence_number"]

    def __str__(self):
        return f"{self.user} - {self.event} - {self.status}"

class EventStatusLog(models.Model):
    registration = models.ForeignKey(EventRegistration, on_delete=models.CASCADE, related_name="status_logs")
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="registration_changes",
    )

    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.registration_id}: {self.old_status} -> {self.new_status}"