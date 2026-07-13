from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views

def home(request):
    return redirect("/home/")

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("events/", include("events.urls")),
    path("registrations/", include("registrations.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("bot/", include("bot.urls")),
    path("standing-orders/", include("standing_orders.urls")),
]

path(
    "password-reset/",
    auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset.html",
        email_template_name="accounts/password_reset_email.html",
        subject_template_name="accounts/password_reset_subject.txt",
        success_url="/password-reset/done/",
    ),
    name="password_reset",
),
path(
    "password-reset/done/",
    auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html",
    ),
    name="password_reset_done",
),
path(
    "reset/<uidb64>/<token>/",
    auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
        success_url="/reset/done/",
    ),
    name="password_reset_confirm",
),
path(
    "reset/done/",
    auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/password_reset_complete.html",
    ),
    name="password_reset_complete",
),