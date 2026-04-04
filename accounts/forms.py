from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "w-full rounded-xl border border-gray-300 px-4 py-3"})
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "w-full rounded-xl border border-gray-300 px-4 py-3"})
    )
    mobile_number = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={"class": "w-full rounded-xl border border-gray-300 px-4 py-3"})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "mobile_number", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update({
            "class": "w-full rounded-xl border border-gray-300 px-4 py-3"
        })
        self.fields["password1"].widget.attrs.update({
            "class": "w-full rounded-xl border border-gray-300 px-4 py-3"
        })
        self.fields["password2"].widget.attrs.update({
            "class": "w-full rounded-xl border border-gray-300 px-4 py-3"
        })