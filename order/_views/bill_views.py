from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django_filters.views import FilterView

from order.filters import BillListFilter
from order.forms import BillCloseForm
from order.models import Bill, StatusBill
from order.queries import get_bills_with_totals, get_orders_display_data
from service.queries import release_tables


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
        context["close_form"] = BillCloseForm()
        return context


@login_required
@require_POST
def close_bill(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if bill.status != StatusBill.OPEN:
        messages.error(request, _("Cannot close a bill that is already closed."))
        return redirect("detail-bill", pk=pk)

    form = BillCloseForm(request.POST, instance=bill)
    if not form.is_valid():
        messages.error(request, _("Invalid form data."))
        return redirect("detail-bill", pk=pk)

    do_print = form.cleaned_data.get("print_bill", False)
    closed_bill = form.save(commit=False)
    closed_bill.status = form.cleaned_data["status"]
    closed_bill.closed_at = timezone.now()
    closed_bill.save(update_fields=["status", "payment_method", "closed_at"])

    msg = ""
    if closed_bill.status == StatusBill.CLOSED:
        closed_bill.refresh_from_db()
        release_tables(closed_bill)
        msg = _("Tables have been released.")

    if do_print:
        # TODO: send task to print Bill
        msg += " " + _("Bill is being prepared for printing.")

    messages.success(
        request,
        _("Bill #%(pk)s has been closed. %(msg)s") % {"pk": bill.pk, "msg": msg},
    )

    return redirect("detail-bill", pk=pk)
