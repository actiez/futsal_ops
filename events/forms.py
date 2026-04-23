from django import forms
from django.utils import timezone
from zoneinfo import ZoneInfo

from .models import Event

SG_TZ = ZoneInfo("Asia/Singapore")


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "start_datetime",
            "end_datetime",
            "location",
            "amount_payable",
            "playing_slots",
            "waiting_slots",
            "backup_slots",
            "status",
        ]
        widgets = {
            "start_datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # IMPORTANT: force correct input format
        self.fields["start_datetime"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["end_datetime"].input_formats = ["%Y-%m-%dT%H:%M"]

        # Convert existing UTC → SG for display
        if self.instance and self.instance.pk:
            if self.instance.start_datetime:
                self.initial["start_datetime"] = timezone.localtime(
                    self.instance.start_datetime, SG_TZ
                ).strftime("%Y-%m-%dT%H:%M")

            if self.instance.end_datetime:
                self.initial["end_datetime"] = timezone.localtime(
                    self.instance.end_datetime, SG_TZ
                ).strftime("%Y-%m-%dT%H:%M")

    def clean(self):
        cleaned_data = super().clean()

        for field in ["start_datetime", "end_datetime"]:
            dt = cleaned_data.get(field)

            if dt and timezone.is_naive(dt):
                # FORCE interpret as Singapore time
                cleaned_data[field] = timezone.make_aware(dt, SG_TZ)

        return cleaned_data