from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from django.conf import settings

def home(request):
    return HttpResponse("HOSTS: " + str(settings.ALLOWED_HOSTS))

urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
]