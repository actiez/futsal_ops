from django.conf import settings
from django.db import models
from events.models import Event


class NotificationLog(models.Model):
    CHANNEL_EMAIL = "email"
    CHANNEL_WHATSAPP = "whatsapp"

    TYPE_CONFIRMATION = "confirmation"
    TYPE_SELECTION = "selection"
    TYPE_REMINDER = "reminder"
    TYPE_CHANGE = "change"

    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    CHANNEL_CHOICES = [
        (CHANNEL_EMAIL, "Email"),
        (CHANNEL_WHATSAPP, "WhatsApp"),
    ]

    TYPE_CHOICES = [
        (TYPE_CONFIRMATION, "Confirmation"),
        (TYPE_SELECTION, "Selection"),
        (TYPE_REMINDER, "Reminder"),
        (TYPE_CHANGE, "Change"),
    ]

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="notification_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_logs")

    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    message_snapshot = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)