from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def home(request):
    return HttpResponse("Futsal Ops is LIVE")

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
]