from django.urls import path
from . import views


urlpatterns = [
    path("message/", views.bot_message, name="bot_message"),
    path("message/", views.bot_message, name="bot_message"),
    path("webhook/", views.meta_webhook, name="meta_webhook"),
]