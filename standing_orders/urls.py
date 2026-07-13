from django.urls import path

from .views import (
    StandingOrderListView,
    StandingOrderDetailView,
    StandingOrderCreateView,
    StandingOrderUpdateView,
    StandingOrderDeleteView,
    StandingOrderRunNowView,
    StandingOrderToggleActiveView,
    RunDueStandingOrdersView,
)


urlpatterns = [
    path("", StandingOrderListView.as_view(), name="standing_order_list"),
    path("new/", StandingOrderCreateView.as_view(), name="standing_order_create"),
    path("<int:pk>/", StandingOrderDetailView.as_view(), name="standing_order_detail"),
    path("<int:pk>/edit/", StandingOrderUpdateView.as_view(), name="standing_order_edit"),
    path("<int:pk>/delete/", StandingOrderDeleteView.as_view(), name="standing_order_delete"),
    path("<int:pk>/run-now/", StandingOrderRunNowView.as_view(), name="standing_order_run_now"),
    path("<int:pk>/toggle-active/", StandingOrderToggleActiveView.as_view(), name="standing_order_toggle_active"),
    path("system/run-due/", RunDueStandingOrdersView.as_view(), name="standing_order_run_due"),
]