from django.urls import path
from .views import EventListView, EventCreateView, EventDetailView, EventUpdateView, EventDeleteView

urlpatterns = [
    path("", EventListView.as_view(), name="event_list"),
    path("create/", EventCreateView.as_view(), name="event_create"),
    path("<int:pk>/", EventDetailView.as_view(), name="event_detail"),
    path("<int:pk>/edit/", EventUpdateView.as_view(), name="event_edit"),
    path("<int:pk>/delete/", EventDeleteView.as_view(), name="event_delete"),
]