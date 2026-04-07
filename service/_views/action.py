from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import ListView

from order.models import Bill, StatusBill


class ActionBillListView(LoginRequiredMixin, ListView):
    model = Bill
    template_name = "service/bill_action_list.html"
    VALID_ACTIONS = {"close-bill", "add-to-order"}

    def get_queryset(self):
        table = self.kwargs.get("table")
        queryset = Bill.objects.filter(
            status=StatusBill.OPEN, table__pk=table
        ).prefetch_related("table", "orders__order_items__item")
        return queryset

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        action = self.kwargs.get("action", "").lower()

        if action not in self.VALID_ACTIONS:
            raise Http404(f"{action} does not exist!")

        data["action"] = action
        return data
