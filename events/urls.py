from django.urls import path
from .calendar import download_event_calendar

from .views import (
    EventListView,
    EventCreateView,
    EventDetailView,
    EventUpdateView,
    EventDeleteView,
    ToggleWeeklyRegistrationLimitView,
    EventCloseoutView,
)

urlpatterns = [
    path("", EventListView.as_view(), name="event_list"),
    path("create/", EventCreateView.as_view(), name="event_create"),
    path("<int:pk>/", EventDetailView.as_view(), name="event_detail"),
    path("<int:pk>/edit/", EventUpdateView.as_view(), name="event_edit"),
    path("<int:pk>/delete/", EventDeleteView.as_view(), name="event_delete"),
    path("<int:pk>/closeout/", EventCloseoutView.as_view(), name="event_closeout"),
    path(
        "<int:pk>/toggle-weekly-limit/",
        ToggleWeeklyRegistrationLimitView.as_view(),
        name="toggle_weekly_limit",
    ),
    path(
    "calendar/<uuid:token>/",
    download_event_calendar,
    name="event_calendar",
),
]