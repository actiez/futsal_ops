from django import forms
from django.utils import timezone
from zoneinfo import ZoneInfo

from .models import Event

SG_TZ = ZoneInfo("Asia/Singapore")

INPUT_CLASS = "w-full rounded-xl border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-black"
SELECT_CLASS = "w-full rounded-xl border border-gray-300 px-4 py-3 bg-white focus:outline-none focus:ring-2 focus:ring-black"


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
            "title": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "start_datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": INPUT_CLASS},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": INPUT_CLASS},
                format="%Y-%m-%dT%H:%M",
            ),
            "location": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "amount_payable": forms.NumberInput(attrs={"class": INPUT_CLASS, "step": "0.01"}),
            "playing_slots": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "waiting_slots": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "backup_slots": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "status": forms.Select(attrs={"class": SELECT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["start_datetime"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["end_datetime"].input_formats = ["%Y-%m-%dT%H:%M"]

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
                cleaned_data[field] = timezone.make_aware(dt, SG_TZ)

        return cleaned_data