from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.views.generic import DetailView
from django_filters.views import FilterView

from order.filters import BillListFilter
from order.models import Bill
from order.queries import get_bills_with_totals, get_orders_display_data


class BillListView(LoginRequiredMixin, FilterView):
    template_name = "order/bill_list.html"
    paginate_by = 25
    filterset_class = BillListFilter

    def get_queryset(self) -> QuerySet[Bill]:
        return get_bills_with_totals()


class BillDetailView(LoginRequiredMixin, DetailView):
    model = Bill
    template_name = "order/bill_detail.html"

    def get_queryset(self):
        return get_bills_with_totals().select_related("waiter")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = context["object"]
        order_items = obj.orders.all()
        items, preparing_time, all_order_status = get_orders_display_data(order_items)
        context["items"] = items
        context["preparing_time"] = preparing_time
        context["all_order_status"] = all_order_status
        return context
