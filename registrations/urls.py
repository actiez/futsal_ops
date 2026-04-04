from django.urls import path
from .views import EventRegistrationCreateView, RegistrationStatusUpdateView, join_event, RegistrationDeleteView

urlpatterns = [
    path("events/<int:event_id>/add/", EventRegistrationCreateView.as_view(), name="registration_add"),
    path("<int:pk>/move/<str:status>/", RegistrationStatusUpdateView.as_view(), name="registration_move"),
    path("join/<uuid:token>/", join_event, name="join_event"),
    path("<int:pk>/delete/", RegistrationDeleteView.as_view(), name="registration_delete"),
    path("join/<uuid:token>/", join_event, name="join_event"),
]