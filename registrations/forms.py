from django import forms
from accounts.models import User


class EventRegistrationAdminForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all().order_by("first_name", "last_name", "username"),
        widget=forms.Select(attrs={"class": "w-full rounded-xl border p-3"})
    )