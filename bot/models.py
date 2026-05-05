from django.conf import settings
from django.db import models


class BotSession(models.Model):
    phone_number = models.CharField(max_length=30, unique=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bot_sessions",
    )

    current_flow = models.CharField(max_length=50)
    step = models.CharField(max_length=50)

    context_data = models.JSONField(default=dict, blank=True)

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} - {self.current_flow} - {self.step}"


class BotMessageLog(models.Model):
    phone_number = models.CharField(max_length=30)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bot_message_logs",
    )

    message_text = models.TextField()
    detected_intent = models.CharField(max_length=50, blank=True)
    action_taken = models.CharField(max_length=100, blank=True)

    reply_text = models.TextField(blank=True)

    ok = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.phone_number} - {self.detected_intent or 'unknown'}"