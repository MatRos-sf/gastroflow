from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from consumers.services import broadcast_item_remove, broadcast_order_remove
from order.models import OrderItem
from service.queries import release_tables_for_open_bill


@login_required
@require_POST
def delete_ordered_item(request: HttpRequest, pk_item: int):
    """
    Remove an ordered item from its order.
    If the order becomes empty, delete it. If the bill then has no orders,
    release the tables and delete the bill.
    """
    item = get_object_or_404(OrderItem, pk=pk_item)
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
