from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET
from django.views.generic import View

from menu.models import Addition, Item
from order.models import Bill
from order.queries import get_recent_unread_notifications
from tools.exceptions import ValidatorError
from tools.session import clear_session


@login_required
def main_menu_view(request):
    return render(request, "service/order_flow/main_menu.html")


@login_required
@require_GET
def unread_notifications_api(request):
    notifications = get_recent_unread_notifications()
    return JsonResponse({"notifications": notifications})


class CartAddView(LoginRequiredMixin, View):
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
            raise ValidatorError(_("Quantity must be an integer!"))

        if quantity < 1:
            raise ValidatorError(_("Quantity must be greater than 0"))
        return quantity

    def _additions_validator(self) -> list[Item]:
        additions_ids = self.request.POST.getlist("additions")
        additions = Addition.objects.filter(id__in=additions_ids)
        if len(additions) != len(additions_ids):
            # capture missing additions
            missing_additions = set(additions_ids) - set(
                additions.values_list("id", flat=True)
            )
            raise ValidatorError(
                _("Some additions were not found, ids: %(ids)s")
                % {"ids": missing_additions},
                missing_additions=missing_additions,
            )
        return additions

    def post(self, request):
        # capture data
        item_id = request.POST.get("item_id", None)
        note = request.POST.get("note", "")
        category = request.GET.get("category")
        if not item_id:
            messages.error(request, _("Item not found"))
            return redirect("service:order-select-items")

        try:
            quantity = self._quantity_validator()
            additions = self._additions_validator()
        except ValidatorError as e:
            messages.error(request, e.message)
            return redirect("service:order-select-items")

        try:
            item = Item.objects.get(pk=item_id)
        except Item.DoesNotExist:
            messages.error(request, _("Item not found"))
            return redirect("service:order-select-items")

        self._add_item_to_cart(item, quantity, note, additions)

        messages.success(request, _("Item added to order"))

        return redirect(f"{reverse('service:order-select-items')}?category={category}")


@login_required
def select_existing_bill(request, pk: int):
    bill = get_object_or_404(Bill, pk=pk)

    request.session["bill"] = pk
    request.session["tables"] = [t.pk for t in bill.table.all()]
    request.session["waiter"] = str(bill.waiter.pk)
    return redirect("service:order-select-items")


@login_required
def remove_item_from_cart(request, index):
    cart = request.session.get("cart", [])
    if cart:
        cart.pop(index)
        request.session["cart"] = cart
        request.session.modified = True
    return redirect("service:order-cart-summary")


@login_required
def clear_cart(request):
    clear_session(request, ["cart", "tables", "waiter", "bill"])
    messages.success(request, _("Order has been cancelled."))

    return redirect("service:main-menu")
