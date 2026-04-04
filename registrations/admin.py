from django.contrib import admin
from .models import EventRegistration, EventStatusLog

admin.site.register(EventRegistration)
admin.site.register(EventStatusLog)