from decimal import ROUND_HALF_UP, Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView, DetailView
from django_filters.views import FilterView

from consumers.services import broadcast_order_remove
from order.filters import BillListFilter
from order.forms import BillCloseForm, BillDiscountForm, BillEditForm
from order.models import Bill, Order, StatusBill, StatusOrder
from order.queries import (
    close_bill_process,
    get_bills_with_totals,
    get_orders_display_data,
)
from service.forms import ChangeBillTableForm
from service.queries import release_tables, release_tables_for_open_bill
from worker.models import Position, Worker


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
        context["discount_form"] = BillDiscountForm()
        context["change_table_form"] = ChangeBillTableForm(
            initial={"table": obj.table.all()}
        )
        context["edit_bill_form"] = BillEditForm(instance=obj)
        context["waiters_with_pin"] = list(
            Worker.objects.filter(position=Position.WAITER, is_active=True)
            .exclude(pin__isnull=True)
            .exclude(pin="")
            .values_list("pk", flat=True)
        )
        total = obj.compute_total
        context["total"] = total
        if obj.discount:
            context["discounted_total"] = (
                total * (1 - Decimal(obj.discount) / 100)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return context


@login_required
@require_POST
def edit_bill(request, pk: int):
    bill = get_object_or_404(Bill, pk=pk)
    if not bill.is_open:
        messages.error(request, _("Cannot edit a closed bill."))
        return redirect("detail-bill", pk=pk)

    form = BillEditForm(request.POST, instance=bill)
    if form.is_valid():
        form.save()
        messages.success(request, _("Bill has been updated."))
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)

    return redirect("detail-bill", pk=pk)


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
    close_bill_process(
        bill, form.cleaned_data["status"], form.cleaned_data["payment_method"]
    )

    msg = ""
    if bill.status == StatusBill.CLOSED:
        release_tables(bill)
        msg = _("Tables have been released.")

    if do_print:
        # TODO: send task to print Bill
        msg += " " + _("Bill is being prepared for printing.")

    messages.success(
        request,
        _("Bill #%(pk)s has been closed. %(msg)s") % {"pk": bill.pk, "msg": msg},
    )

    return redirect("detail-bill", pk=pk)


@login_required
@require_POST
def close_bill_with_release(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if bill.status != StatusBill.CLOSED_AND_OCCUPIED:
        messages.error(
            request,
            _(
                "Cannot close bill and release tables when status bill is different than closed and occupied."
            ),
        )
        return redirect("detail-bill", pk=pk)

    close_bill_process(bill, StatusBill.CLOSED)
    release_tables(bill)

    messages.success(
        request,
        _("Bill #%(pk)s has been closed and tables have been released.")
        % {"pk": bill.pk},
    )

    return redirect("detail-bill", pk=pk)


@login_required
@require_POST
def add_discount(request, pk: int):
    """
    Update discount field for bill. Only allowed when bill is open.
    """
    bill = get_object_or_404(Bill, pk=pk)
    if bill.status != StatusBill.OPEN:
        messages.error(request, _("Cannot add a discount to a bill that is not open."))
        return redirect("detail-bill", pk=pk)

    form = BillDiscountForm(request.POST, instance=bill)
    if not form.is_valid():
        messages.error(request, _("Invalid form data. Discount must be 0–100."))
        return redirect("detail-bill", pk=pk)

    form.save()

    messages.success(request, _("Discount has been applied."))
    return redirect("detail-bill", pk=pk)


class BillDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Bill
    success_url = reverse_lazy("list-bill")

    def test_func(self):
        self.object = self.get_object()
        if self.object.status == StatusBill.OPEN:
            return True
        elif self.request.user.is_superuser:
            return True
        messages.error(
            self.request,
            _(
                "You cannot delete a bill that is not open. Only superusers can delete bills."
            ),
        )
        return False

    def _remove_order(self, order: Order):
        order_pk = order.pk
        order_status = order.status
        order.delete()
        if order_status in [StatusOrder.ORDER, StatusOrder.PREPARING]:
            broadcast_order_remove(order_pk)

    def post(self, request, *args, **kwargs):
        bill_pk = self.object.pk
        orders = self.object.orders.all()

        for order in orders:
            self._remove_order(order)

        release_tables_for_open_bill(self.object)
        messages.success(request, _("Removed bill %(pk)s.") % {"pk": bill_pk})
        return super().post(request, *args, **kwargs)
