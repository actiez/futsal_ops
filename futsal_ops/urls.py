from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def home(request):
    return redirect("/home/")

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("events/", include("events.urls")),
    path("registrations/", include("registrations.urls")),
    path("dashboard/", include("dashboard.urls")),
]