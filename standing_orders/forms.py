from django import forms

from .models import StandingOrder
from .services import refresh_next_run_at


FIELD_CLASS = (
    "w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-emerald-500"
)


class StandingOrderForm(forms.ModelForm):
    weekly_limit_enabled = forms.TypedChoiceField(
        required=False,
        choices=[
            ("", "---------"),
            ("true", "Turn ON"),
            ("false", "Turn OFF"),
        ],
        coerce=lambda value: (
            True if value == "true"
            else False if value == "false"
            else None
        ),
        empty_value=None,
        widget=forms.Select(attrs={
            "class": FIELD_CLASS,
        }),
    )

    class Meta:
        model = StandingOrder
        fields = [
            "name",
            "action",
            "frequency",
            "run_day_of_week",
            "run_time",
            "is_active",

            "event_day_of_week",
            "event_start_time",
            "event_end_time",
            "location",
            "amount_payable",
            "playing_slots",
            "waiting_slots",
            "backup_slots",
            "is_private",
            "leave_cutoff_minutes",

            "weekly_limit_enabled",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": FIELD_CLASS,
                "placeholder": "e.g. Create Wednesday Futsal",
            }),
            "action": forms.Select(attrs={
                "class": FIELD_CLASS,
            }),
            "frequency": forms.Select(attrs={
                "class": FIELD_CLASS,
            }),
            "run_day_of_week": forms.Select(attrs={
                "class": FIELD_CLASS,
            }),
            "run_time": forms.TimeInput(attrs={
                "type": "time",
                "class": FIELD_CLASS,
            }),
            "event_day_of_week": forms.Select(attrs={
                "class": FIELD_CLASS,
            }),
            "event_start_time": forms.TimeInput(attrs={
                "type": "time",
                "class": FIELD_CLASS,
            }),
            "event_end_time": forms.TimeInput(attrs={
                "type": "time",
                "class": FIELD_CLASS,
            }),
            "location": forms.TextInput(attrs={
                "class": FIELD_CLASS,
                "placeholder": "e.g. CCK Sports Hall",
            }),
            "amount_payable": forms.NumberInput(attrs={
                "step": "0.01",
                "class": FIELD_CLASS,
            }),
            "playing_slots": forms.NumberInput(attrs={
                "class": FIELD_CLASS,
            }),
            "waiting_slots": forms.NumberInput(attrs={
                "class": FIELD_CLASS,
            }),
            "backup_slots": forms.NumberInput(attrs={
                "class": FIELD_CLASS,
            }),
            "leave_cutoff_minutes": forms.Select(attrs={
                "class": FIELD_CLASS,
            }),
        }

        labels = {
            "leave_cutoff_minutes": "Disable self-leaving before kick-off",
        }

        help_texts = {
            "leave_cutoff_minutes": (
                "Events created by this standing order will use this self-leaving cutoff. "
                "Admins can still remove or manage players manually."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["leave_cutoff_minutes"].required = False

    def clean(self):
        cleaned_data = super().clean()

        action = cleaned_data.get("action")

        if action == StandingOrder.ACTION_CREATE_EVENT:
            required_fields = [
                "event_day_of_week",
                "event_start_time",
                "event_end_time",
                "location",
                "amount_payable",
                "playing_slots",
                "waiting_slots",
                "backup_slots",
            ]

            for field in required_fields:
                if cleaned_data.get(field) in [None, ""]:
                    self.add_error(field, "Required for create event standing orders.")

        if action == StandingOrder.ACTION_SET_WEEKLY_LIMIT:
            if cleaned_data.get("weekly_limit_enabled") is None:
                self.add_error(
                    "weekly_limit_enabled",
                    "Required for weekly limit standing orders.",
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()
            refresh_next_run_at(instance)

        return instance