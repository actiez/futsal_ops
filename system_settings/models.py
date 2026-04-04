from django.db import models


class SystemSettings(models.Model):
    default_playing_slots = models.PositiveIntegerField(default=15)
    default_waiting_slots = models.PositiveIntegerField(default=5)
    default_backup_slots = models.PositiveIntegerField(default=3)

    default_location = models.CharField(max_length=255, blank=True, default="Keat Hong Gardens (Opposite BLK 815 CCK Ave 7)")
    default_amount_payable = models.DecimalField(max_digits=8, decimal_places=2, default=2.00)

    default_start_time = models.TimeField(null=True, blank=True)
    default_end_time = models.TimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "System Settings"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj