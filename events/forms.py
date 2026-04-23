from datetime import datetime

from django import forms
from django.utils import timezone
from zoneinfo import ZoneInfo

from .models import Event

SG_TZ = ZoneInfo("Asia/Singapore")

INPUT_CLASS = "w-full rounded-xl border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-black"
SELECT_CLASS = "w-full rounded-xl border border-gray-300 px-4 py-3 bg-white focus:outline-none focus:ring-2 focus:ring-black"


class EventForm(forms.ModelForm):
    event_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": INPUT_CLASS})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time", "class": INPUT_CLASS})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time", "class": INPUT_CLASS})
    )

    class Meta:
        model = Event
        fields = [
            "title",
            "event_date",
            "start_time",
            "end_time",
            "location",
            "amount_payable",
            "playing_slots",
            "waiting_slots",
            "backup_slots",
            "status",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "location": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "amount_payable": forms.NumberInput(
                attrs={"class": INPUT_CLASS, "step": "0.01"}
            ),
            "playing_slots": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "waiting_slots": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "backup_slots": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "status": forms.Select(attrs={"class": SELECT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            if self.instance.start_datetime:
                local_start = timezone.localtime(self.instance.start_datetime, SG_TZ)
                self.initial["event_date"] = local_start.date()
                self.initial["start_time"] = local_start.strftime("%H:%M")

            if self.instance.end_datetime:
                local_end = timezone.localtime(self.instance.end_datetime, SG_TZ)
                self.initial["end_time"] = local_end.strftime("%H:%M")

    def clean(self):
        cleaned_data = super().clean()

        event_date = cleaned_data.get("event_date")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if event_date and start_time:
            start_dt = datetime.combine(event_date, start_time)
            cleaned_data["start_datetime"] = start_dt

        if event_date and end_time:
            end_dt = datetime.combine(event_date, end_time)
            cleaned_data["end_datetime"] = end_dt

        start_datetime = cleaned_data.get("start_datetime")
        end_datetime = cleaned_data.get("end_datetime")

        if start_datetime and end_datetime and end_datetime <= start_datetime:
            self.add_error("end_time", "End time must be later than start time.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        start_dt = self.cleaned_data["start_datetime"]
        end_dt = self.cleaned_data["end_datetime"]

        # Let Django interpret these naive datetimes in project TIME_ZONE
        instance.start_datetime = start_dt
        instance.end_datetime = end_dt

        if commit:
            instance.save()

        return instance