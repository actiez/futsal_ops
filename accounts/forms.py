from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


INPUT_CLASS = "w-full rounded-xl border border-gray-300 px-4 py-3"


def normalize_mobile_number(value):
    cleaned = (value or "").strip()

    cleaned = (
        cleaned
        .replace("+", "")
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    if cleaned.startswith("65") and len(cleaned) == 10:
        cleaned = cleaned[2:]

    return cleaned


class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": INPUT_CLASS}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": INPUT_CLASS}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": INPUT_CLASS}),
    )
    mobile_number = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "e.g. 91234567",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "mobile_number",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update({"class": INPUT_CLASS})
        self.fields["password1"].widget.attrs.update({"class": INPUT_CLASS})
        self.fields["password2"].widget.attrs.update({"class": INPUT_CLASS})

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()

        if not email:
            raise forms.ValidationError("Email is required.")

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already used by another account.")

        return email

    def clean_mobile_number(self):
        mobile = normalize_mobile_number(self.cleaned_data.get("mobile_number"))

        if not mobile:
            raise forms.ValidationError("Mobile number is required.")

        if not mobile.isdigit() or len(mobile) != 8:
            raise forms.ValidationError("Please enter a valid 8-digit Singapore mobile number.")

        if User.objects.filter(mobile_number=mobile).exists():
            raise forms.ValidationError("This mobile number is already used by another account.")

        return mobile


class UserProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": INPUT_CLASS}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": INPUT_CLASS}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": INPUT_CLASS}),
    )
    mobile_number = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "e.g. 91234567",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "mobile_number")

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()

        if not email:
            raise forms.ValidationError("Email is required.")

        qs = User.objects.filter(email__iexact=email)

        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("This email is already used by another account.")

        return email

    def clean_mobile_number(self):
        mobile = normalize_mobile_number(self.cleaned_data.get("mobile_number"))

        if not mobile:
            raise forms.ValidationError("Mobile number is required.")

        if not mobile.isdigit() or len(mobile) != 8:
            raise forms.ValidationError("Please enter a valid 8-digit Singapore mobile number.")

        qs = User.objects.filter(mobile_number=mobile)

        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("This mobile number is already used by another account.")

        return mobile