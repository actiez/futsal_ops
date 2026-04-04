from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("events/", include("events.urls")),
    path("registrations/", include("registrations.urls")),
    path("notifications/", include("notifications.urls")),
    path("settings/", include("system_settings.urls")),
]