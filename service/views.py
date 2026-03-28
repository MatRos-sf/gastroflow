import logging

from django.contrib import messages
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import View

from consumers.services import broadcast_change_table
from menu.models import Item, MenuType
from order.forms import ChangeBillTableForm
from order.models import Bill, Notification, NotificationStatus
from tools.session import clear_session

logger = logging.getLogger(__name__)


class ValidatorError(Exception):
    """Custom validation error for invalid or missing session/bill data"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message)
        self.more_data = kwargs
        self.message = message


def menu_waiter(request):
    return render(request, "service/order_flow/menu_waiter.html")


class CartAddView(View):
    def _add_item_to_cart(
        self, item: Item, quantity: int, note: str, additions: list[Item]
    ):
        cart = self.request.session.get("cart", [])
        cart.append(
            {
                "item_id": item.id,
                "name": item.name,
                "price": str(item.price),
                "quantity": quantity,
                "note": note,
                "additions": [
                    {"id": a.id, "name": a.name, "price": str(a.price)}
                    for a in additions
                ],
                "preparation_location": item.preparation_location,
            }
        )
        self.request.session["cart"] = cart
        self.request.session.modified = True

    def _quantity_validator(self) -> int:
        try:
            quantity = int(self.request.POST.get("quantity", 1))
        except ValueError:
            raise ValidatorError("Ilość musi być liczbą całkowitą!")

        if quantity < 1:
            raise ValidatorError("Ilość musi być większa niż 0")
        return quantity

    def _additions_validator(self) -> list[Item]:
        additions_ids = self.request.POST.getlist("additions")
        additions = Item.objects.filter(id__in=additions_ids)
        if len(additions) != len(additions_ids):
            # capture missing additions
            missing_additions = set(additions_ids) - set(
                additions.values_list("id", flat=True)
            )
            raise ValidatorError(
                f"Nie znaleziono wszystkich dodatków, o id: {missing_additions}",
                missing_additions=missing_additions,
            )
        return additions

    def post(self, request):
        # capture data
        item_id = request.POST.get("item_id")
        note = request.POST.get("note", "")
        category = request.GET.get("category", MenuType.MAIN)

        try:
            quantity = self._quantity_validator()
            additions = self._additions_validator()
        except ValidatorError as e:
            messages.error(request, e.message)
            return redirect("service:order-select-items")

        try:
            item = Item.objects.get(pk=item_id)
        except Item.DoesNotExist:
            messages.error(request, "Nie znaleziono produktu")
            return redirect("service:order-select-items")

        self._add_item_to_cart(item, quantity, note, additions)

        messages.success(request, "Dodano danie do zamówienia")

        return redirect(f"{reverse('service:order-select-items')}?category={category}")


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


def add_order_to_bill(request, pk: int):
    bill = Bill.objects.get(pk=pk)
    if not bill:
        return HttpResponseNotFound("<h1>Page not found!</h1>")
    request.session["bill"] = pk
    request.session["tables"] = [t.pk for t in bill.table.all()]
    request.session["waiter"] = str(bill.service.pk)
    return redirect("service:order-select-items")


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
