from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django_filters.views import FilterView

from consumers.services import broadcast_item_remove, broadcast_order_remove
from order.filters import OrderFilter
from order.models import Bill, Location, Order, OrderItem, OrderItemStatus, StatusBill
from service.models import Table
from service.queries import release_tables_for_open_bill


def can_delete_bill(request: HttpRequest, bill: Bill) -> bool:
    if bill.status == StatusBill.OPEN:
        return True
    return request.user.is_superuser


@login_required
@require_POST
def delete_order(request: HttpRequest, pk: int):
    order = get_object_or_404(Order, pk=pk)
    bill = order.bill
    if not can_delete_bill(request, bill):
        messages.error(request, _("You do not have permission to delete this order."))
        return redirect("detail-bill", pk=bill.pk)

    order.delete()
    messages.success(request, _("Removed %(pk)s.") % {"pk": pk})
    broadcast_order_remove(pk)

    if bill.orders.count() == 0:
        release_tables_for_open_bill(bill)
        bill.delete()
        messages.success(request, _("Removed empty bill %(pk)s.") % {"pk": bill.pk})
        return redirect("list-bill")

    return redirect("detail-bill", pk=bill.pk)


@login_required
@require_POST
def delete_ordered_item(request: HttpRequest, pk_item: int):
    """
    Remove an ordered item from its order.
    If the order becomes empty, delete it. If the bill then has no orders,
    release the tables and delete the bill.
    """
    item = get_object_or_404(OrderItem, pk=pk_item)
    bill = item.order.bill
    if not can_delete_bill(request, bill):
        messages.error(request, _("You do not have permission to delete this item."))
        return redirect("detail-bill", pk=bill.pk)

    item_name = item.name_snapshot
    item_location = item.order.category
    order = item.order
    item.delete()
    messages.success(request, _("Removed %(name)s.") % {"name": item_name})
    broadcast_item_remove(order.pk, pk_item, item_location)

    if order.order_items.count() == 0:
        order_pk = order.pk
        bill = order.bill
        order.delete()
        broadcast_order_remove(order_pk)
        messages.success(request, _("Removed empty order %(pk)s.") % {"pk": order_pk})
        if bill.orders.count() == 0:
            bill_pk = bill.pk
            release_tables_for_open_bill(bill)
            messages.success(request, _("Tables have been released."))
            bill.delete()
            messages.success(request, _("Removed empty bill %(pk)s.") % {"pk": bill_pk})

            return redirect("list-bill")

    return redirect("detail-bill", pk=order.bill.pk)


class ReadyOrderListView(LoginRequiredMixin, FilterView):
    """Basic view show previous preparing orders"""

    model = Order
    template_name = "order/order_ready_history.html"
    context_object_name = "items"
    filterset_class = OrderFilter
    paginate_by = 20

    def get_queryset(self):
        return (
            Order.objects.select_related("bill")
            .prefetch_related(
                "order_items",
                "order_items__order_item_additions",
                Prefetch("bill__table", queryset=Table.objects.select_related("hall")),
            )
            .filter(status=OrderItemStatus.READY)
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Location.values
        ctx["today"] = timezone.localdate().strftime("%Y-%m-%d")
        return ctx
