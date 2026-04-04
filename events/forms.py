from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime

from .models import Event


class EventForm(forms.ModelForm):
    event_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "w-full rounded-xl border p-3"})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time", "class": "w-full rounded-xl border p-3"})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time", "class": "w-full rounded-xl border p-3"})
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
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "w-full rounded-xl border p-3"}),
            "location": forms.TextInput(attrs={"class": "w-full rounded-xl border p-3"}),
            "amount_payable": forms.NumberInput(attrs={"class": "w-full rounded-xl border p-3", "step": "0.01"}),
            "playing_slots": forms.NumberInput(attrs={"class": "w-full rounded-xl border p-3"}),
            "waiting_slots": forms.NumberInput(attrs={"class": "w-full rounded-xl border p-3"}),
           
        }

    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        event_instance = kwargs.get("instance")

        if event_instance:
            initial["event_date"] = event_instance.start_datetime.date()
            initial["start_time"] = event_instance.start_datetime.time().replace(second=0, microsecond=0)
            initial["end_time"] = event_instance.end_datetime.time().replace(second=0, microsecond=0)

        kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        event_date = cleaned_data.get("event_date")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if event_date and start_time and end_time:
            start_dt = datetime.combine(event_date, start_time)
            end_dt = datetime.combine(event_date, end_time)

            if end_dt <= start_dt:
                raise ValidationError("End time must be after start time.")

            cleaned_data["start_datetime"] = start_dt
            cleaned_data["end_datetime"] = end_dt

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.start_datetime = self.cleaned_data["start_datetime"]
        instance.end_datetime = self.cleaned_data["end_datetime"]

        if commit:
            instance.save()

        return instance