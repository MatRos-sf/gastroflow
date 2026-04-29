import logging
from typing import Iterable

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from consumers.serializers import serialize_order
from menu.models import Item, Location
from order.models import Bill, Order, OrderItem, OrderItemAddition
from service.exceptions import StockError, ValidatorError
from service.models import Table
from tools.session import SessionInfo, clear_session, split_items_by_location
from worker.models import Worker
from worker.queries import get_workers_clocked_in_today

logger = logging.getLogger(__name__)


@transaction.atomic
def create_order(bill: Bill, items: Iterable[dict], **kwargs):
    if not items:
        return
    order = Order.objects.create(bill=bill, **kwargs)

    for item in items:
        menu_item = (
            Item.objects.select_for_update().only("daily_stock").get(pk=item["item_id"])
        )
        if menu_item.daily_stock is not None:
            if menu_item.daily_stock < item["quantity"]:
                raise StockError(item["name"], menu_item.daily_stock)
            Item.objects.filter(pk=menu_item.pk).update(
                daily_stock=F("daily_stock") - item["quantity"]
            )

        order_item = OrderItem.objects.create(
            order=order,
            item_id=item["item_id"],
            name_snapshot=item["name"],
            price_snapshot=item["price"],
            quantity=item["quantity"],
            note=item["note"],
        )
        for addition in item["additions"]:
            OrderItemAddition.objects.create(
                order_item=order_item,
                addition_id=addition["id"],
                name_snapshot=addition["name"],
                price_snapshot=addition["price"],
                quantity=item["quantity"],
            )

    group_name = (
        "kitchen_orders" if kwargs["category"] == Location.KITCHEN else "bar_orders"
    )
    _broadcast_new_order(order, group_name)


def _broadcast_new_order(order: Order, group_name: str) -> None:
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {"type": "new_order", "order_data": serialize_order(order)},
    )


class CartSummaryView(View):
    template_name = "service/order_flow/cart_summary.html"

    def get(self, request):
        cart = request.session.get("cart", [])
        waiters = get_workers_clocked_in_today(
            values=["pk", "first_name", "last_name", "pin"]
        )
        waiters_with_pin = list(
            waiters.exclude(pin__isnull=True)
            .exclude(pin="")
            .values_list("pk", flat=True)
        )
        return render(
            request,
            self.template_name,
            {
                "cart": cart,
                "waiters": waiters,
                "selected_waiter": request.session.get("waiter"),
                "waiters_with_pin": waiters_with_pin,
            },
        )

    def _get_session_info(self) -> SessionInfo:
        return SessionInfo(
            self.request.session.get("cart", []),
            self.request.session.get("tables", []),
            self.request.session.get("waiter"),
            self.request.session.get("bill"),
        )

    def _missing_required_session_data(
        self, cart: None | list, waiter: None | str, tables: None | list
    ) -> bool:
        return not (cart and waiter and tables)

    def _get_or_create_bill_model(
        self,
        bill: int | None,
        tables: list,
        waiter: int,
        note: str,
        guest_count: int | None,
    ) -> Bill:
        if bill:
            try:
                return Bill.objects.get(pk=bill)
            except Bill.DoesNotExist:
                messages.error(self.request, _("Bill not found"))
                raise ValidatorError("Bill not found")
        bill_instance = Bill.objects.create(
            waiter_id=waiter, note=note, guest_count=guest_count
        )
        bill_instance.table.add(*tables)
        return bill_instance

    def _delegate_orders(self, bill: Bill, cart: list):
        kitchen, bar = split_items_by_location(cart)
        create_order(bill, list(kitchen), category=Location.KITCHEN)
        create_order(bill, list(bar), category=Location.BAR)

    def _change_tables_status(self, tables: list):
        Table.objects.filter(pk__in=tables).update(is_occupied=True)

    def _validate_pin(self, waiter_pk: str) -> None:
        """Raise ValidatorError when the waiter has a PIN and the submitted PIN is wrong."""
        try:
            worker = Worker.objects.get(pk=waiter_pk)
        except Worker.DoesNotExist:
            raise ValidatorError(_("Waiter not found"))
        if worker.pin:
            submitted = self.request.POST.get("pin", "")
            if submitted != worker.pin:
                raise ValidatorError(_("Invalid PIN"))

    def _guest_count_validator(self) -> int:
        try:
            guest_count = int(self.request.POST.get("guest_count", 1))
        except ValueError:
            raise ValidatorError(_("Guest count must be an integer!"))
        if guest_count < 1:
            raise ValidatorError(_("Guest count must be greater than 0"))
        return guest_count

    def post(self, request):
        """
        1. Read session data
        2. Validate guest count and required fields
        3. Atomically: resolve/create bill → create orders (with stock check) → mark tables occupied
        4. Clear session, redirect
        """
        waiter_from_form = request.POST.get("waiter", "")
        if waiter_from_form:
            request.session["waiter"] = waiter_from_form

        session_info = self._get_session_info()
        note = request.POST.get("note", "")
        is_init_bill = not session_info.bill
        guest_count: None | int = None

        if is_init_bill:
            try:
                guest_count = self._guest_count_validator()
            except ValidatorError as e:
                messages.error(request, str(e))
                return redirect("service:order-cart-summary")

        if session_info.waiter:
            try:
                self._validate_pin(session_info.waiter)
            except ValidatorError as e:
                messages.error(request, str(e))
                return redirect("service:order-cart-summary")

        if self._missing_required_session_data(
            session_info.cart, session_info.waiter, session_info.tables
        ):
            messages.error(request, _("Missing required session data"))
            return redirect("service:order-cart-summary")

        try:
            with transaction.atomic():
                bill = self._get_or_create_bill_model(
                    session_info.bill,
                    session_info.tables,
                    session_info.waiter,
                    note,
                    guest_count,
                )
                self._delegate_orders(bill, session_info.cart)
                self._change_tables_status(session_info.tables)
        except ValidatorError:
            return redirect("service:order-cart-summary")
        except StockError as e:
            if e.available == 0:
                messages.error(
                    request, _("%(item)s is sold out.") % {"item": e.item_name}
                )
            else:
                messages.error(
                    request,
                    _("%(item)s: only %(n)d portion(s) left.")
                    % {
                        "item": e.item_name,
                        "n": e.available,
                    },
                )
            return redirect("service:order-cart-summary")
        except Exception:
            logger.exception("Failed to delegate orders")
            messages.error(request, _("An error occurred while creating the order"))
            return redirect("service:order-cart-summary")

        url = reverse("detail-bill", args=[bill.pk])
        label = (
            _("Order #%(pk)s completed.")
            if is_init_bill
            else _("Order #%(pk)s updated.")
        )
        messages.success(
            request,
            mark_safe(
                f'<a href="{url}" class="alert-link">{label % {"pk": bill.pk}}</a>'
            ),
        )
        logger.info("Bill #%s created by waiter %s", bill.pk, session_info.waiter)
        clear_session(self.request, ["cart", "tables", "waiter", "bill"])
        return redirect("service:main-menu")
