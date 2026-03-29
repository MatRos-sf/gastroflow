import logging

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from consumers.services import broadcast_change_table
from order.forms import ChangeBillTableForm
from order.models import Bill, Notification, NotificationStatus
from tools.session import clear_session

logger = logging.getLogger(__name__)


def menu_waiter(request):
    return render(request, "service/order_flow/menu_waiter.html")


def api_remove_from_cart(request, index):
    cart = request.session.get("cart", [])
    if cart:
        del_item = cart.pop(index)
        request.session["cart"] = cart
        request.session.modified = True
        print("Deleted item:", del_item)
    return redirect("service:order-cart-summary")


def clear_cart(request):
    clear_session(request, ["cart", "tables", "waiter", "bill"])
    messages.success(request, "Zamówienie zostało anulowane!")

    return redirect("service:menu-waiter")


def check_notifications(request):
    has_new = Notification.objects.filter(
        status=NotificationStatus.WAITING_TO_READ
    ).exists()
    return JsonResponse({"has_new": has_new})


def change_table(request, pk: int):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == "POST":
        form = ChangeBillTableForm(request.POST)
        if form.is_valid():
            form.save(bill)
            messages.success(request, "Stolik został zmieniony!")
            new_table = bill.str_tables()
            for order in bill.orders.all():
                broadcast_change_table(order.pk, new_table)
            return redirect(bill.get_absolute_url())
    else:
        form = ChangeBillTableForm(initial={"table": bill.table.all()})

    return render(request, "service/change_table.html", {"form": form})
