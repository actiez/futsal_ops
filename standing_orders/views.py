from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView

from core.mixins import AdminRequiredMixin

from .forms import StandingOrderForm
from .models import StandingOrder, StandingOrderRunLog
from .services import run_standing_order, refresh_next_run_at

from django.conf import settings
from django.http import JsonResponse

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

class StandingOrderListView(AdminRequiredMixin, ListView):
    model = StandingOrder
    template_name = "standing_orders/list.html"
    context_object_name = "standing_orders"

    def get_queryset(self):
        return (
            StandingOrder.objects
            .all()
            .order_by("-is_active", "run_day_of_week", "run_time", "name")
        )


class StandingOrderDetailView(AdminRequiredMixin, DetailView):
    model = StandingOrder
    template_name = "standing_orders/detail.html"
    context_object_name = "standing_order"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["run_logs"] = (
            StandingOrderRunLog.objects
            .filter(standing_order=self.object)
            .select_related("created_event")
            .order_by("-ran_at")[:20]
        )
        return context


class StandingOrderCreateView(AdminRequiredMixin, CreateView):
    model = StandingOrder
    form_class = StandingOrderForm
    template_name = "standing_orders/form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        refresh_next_run_at(self.object)

        messages.success(self.request, "Standing order created.")
        return response

    def get_success_url(self):
        return reverse_lazy("standing_order_detail", kwargs={"pk": self.object.pk})


class StandingOrderUpdateView(AdminRequiredMixin, UpdateView):
    model = StandingOrder
    form_class = StandingOrderForm
    template_name = "standing_orders/form.html"

    def form_valid(self, form):
        response = super().form_valid(form)

        refresh_next_run_at(self.object)

        messages.success(self.request, "Standing order updated.")
        return response

    def get_success_url(self):
        return reverse_lazy("standing_order_detail", kwargs={"pk": self.object.pk})


class StandingOrderDeleteView(AdminRequiredMixin, DeleteView):
    model = StandingOrder
    template_name = "standing_orders/delete.html"
    success_url = reverse_lazy("standing_order_list")

    def form_valid(self, form):
        messages.success(self.request, "Standing order deleted.")
        return super().form_valid(form)


class StandingOrderRunNowView(AdminRequiredMixin, View):
    def post(self, request, pk):
        standing_order = StandingOrder.objects.get(pk=pk)

        log = run_standing_order(standing_order)

        if log.status == StandingOrderRunLog.STATUS_SUCCESS:
            messages.success(request, log.message)
        elif log.status == StandingOrderRunLog.STATUS_SKIPPED:
            messages.info(request, log.message)
        else:
            messages.error(request, log.message)

        return redirect("standing_order_detail", pk=standing_order.pk)


class StandingOrderToggleActiveView(AdminRequiredMixin, View):
    def post(self, request, pk):
        standing_order = StandingOrder.objects.get(pk=pk)
        standing_order.is_active = not standing_order.is_active
        standing_order.save(update_fields=["is_active", "updated_at"])

        refresh_next_run_at(standing_order)

        if standing_order.is_active:
            messages.success(request, "Standing order activated.")
        else:
            messages.info(request, "Standing order paused.")

        return redirect("standing_order_detail", pk=standing_order.pk)
    
@method_decorator(csrf_exempt, name="dispatch")
class RunDueStandingOrdersView(View):
    def post(self, request):
        expected_token = getattr(settings, "STANDING_ORDER_CRON_TOKEN", "")
        provided_token = (
            request.POST.get("token")
            or request.headers.get("X-Standing-Order-Token")
        )

        if not expected_token or provided_token != expected_token:
            return JsonResponse(
                {
                    "ok": False,
                    "error": "Unauthorized",
                },
                status=403,
            )

        from .services import run_due_standing_orders

        logs = run_due_standing_orders()

        return JsonResponse({
            "ok": True,
            "run_count": len(logs),
            "logs": [
                {
                    "standing_order": log.standing_order.name,
                    "status": log.status,
                    "message": log.message,
                    "ran_at": log.ran_at.isoformat(),
                    "created_event_id": log.created_event_id,
                }
                for log in logs
            ],
        })