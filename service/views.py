import logging
from typing import Iterable, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.db.models import Q, QuerySet
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, View

from menu.models import Item, Location, MenuType
from order.models import (
    Bill,
    Notification,
    NotificationStatus,
    Order,
    OrderItem,
    OrderItemAddition,
    PaymentMethod,
    StatusBill,
)
from tools.session import SessionInfo, clear_session, split_items_by_location
from worker.models import Position, Worker

from .models import Table

logger = logging.getLogger(__name__)


class ValidatorError(Exception):
    """Custom validation error for invalid or missing session/bill data"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message)
        self.more_data = kwargs
        self.message = message


def menu_waiter(request):
    return render(request, "service/menu_waiter.html")


class MenuWaiterView(ListView):
    model = Item
    template_name = "service/menu_cards/items_waiter.html"

    def get_queryset(self):
        raw_category = self.request.GET.get("category", MenuType.MAIN)
        category = self._validated_category(raw_category)
        return Item.objects.exclude(menu=MenuType.UNAVAILABLE).filter(menu=category)

    def get_template_names(self):
        """
        Return list of template names. Kept as hook for future template selection (e.g. user preferences).
        """
        # TODO: If in future you want multiple fallbacks, return a list here.
        return [self.template_name]

    def get_context_data(self, **kwargs):
        """
        Build extra context:
            * selected_category: currently selected category
            * items_no_sub: items without sub_menu
            * sub_menu_groups: dict mapping sub_menu -> list of items
            * categories: list of (value,label) for nav
        """
        category = self.request.GET.get("category", MenuType.MAIN)
        context = super().get_context_data(**kwargs)
        context["selected_category"] = category

        qs = context["object_list"]
        items_no_sub = qs.filter(sub_menu__isnull=True)
        items_with_sub = qs.exclude(sub_menu__isnull=True).order_by("sub_menu")

        sub_menu_groups: dict[str, QuerySet] = dict()
        for sub in items_with_sub.values_list("sub_menu", flat=True).distinct():
            sub_menu_groups[sub] = items_with_sub.filter(sub_menu=sub)

        context["categories"] = [
            (value, label)
            for value, label in MenuType.choices
            if value != MenuType.UNAVAILABLE
        ]
        context["items_no_sub"] = items_no_sub
        context["sub_menu_groups"] = sub_menu_groups

        return context

    def _validated_category(self, category: str) -> str:
        """Return a valid category value - if provided category isn't valid, return the default MenuType.Main and error message"""
        if category not in MenuType.values:
            messages.error(self.request, f"Invalid category: {category}")
            return MenuType.MAIN
        return category


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
            return redirect("service:items-waiter")

        try:
            item = Item.objects.get(pk=item_id)
        except Item.DoesNotExist:
            messages.error(request, "Nie znaleziono produktu")
            return redirect("service:items-waiter")

        self._add_item_to_cart(item, quantity, note, additions)

        messages.success(request, "Dodano danie do zamówienia")

        return redirect(f"{reverse('service:items-waiter')}?category={category}")


class CardView(View):
    template_name = "service/cart_waiter.html"

    # TODO: test this class
    def get(self, request):
        cart = request.session.get("cart", [])
        return render(request, self.template_name, {"cart": cart})

    def _get_session_info(self) -> SessionInfo:
        """Capture all information from user session"""
        return SessionInfo(
            self.request.session.get("cart", []),
            self.request.session.get("tables", []),
            self.request.session.get("waiter"),
            self.request.session.get("bill"),
        )

    def _missing_required_session_data(
        self, cart: None | list, waiter: None | str, tables: None | list
    ) -> bool:
        """Return True when missing required session data"""
        return not (cart and waiter and tables)

    def _capture_bill_model(
        self, bill: int, tables: list, waiter: int, note: str
    ) -> Bill:
        if bill:
            try:
                bill_instance = Bill.objects.get(pk=bill)
            except Bill.DoesNotExist:
                messages.error(self.request, "Nie znaleziono rachunku")
                raise ValidatorError("Nie znaleziono rachunku")
        else:
            bill_instance = Bill.objects.create(service_id=waiter, note=note)
            bill_instance.table.add(*tables)
        return bill_instance

    def _delegate_orders(self, bill: Bill, cart: list):
        """Delegate orders to kitchen and bar"""
        # TODO: here should be something like choose option in db user if user has accept bar and kitchen do all
        kitchen, bar = split_items_by_location(cart)
        create_order(
            bill, list(kitchen), category=Location.KITCHEN
        )  # TODO: Change category to preparation_location
        create_order(bill, list(bar), category=Location.BAR)

        # TODO: Send real-time notification to kitchen and bar via Django Channels

    def _change_tables_status(self, tables: list):
        Table.objects.filter(pk__in=tables).update(is_occupied=True)

    def post(self, request):
        """
        After press submit button, there are following step:
            1. Import session data
            2. Check requirements
            3. Capture bill model
            4. Delegate orders to kitchen and bar
            5. Change tables status to occurred
            6. Clear session
        """
        session_info = self._get_session_info()
        note = request.POST.get("note", "")

        if self._missing_required_session_data(
            session_info.cart, session_info.waiter, session_info.tables
        ):
            messages.error(request, "Brak wymaganych danych w sesji")
            return redirect("service:cart")

        try:
            bill = self._capture_bill_model(
                session_info.bill, session_info.tables, session_info.waiter, note
            )
        except ValidatorError:
            return redirect("service:cart")

        # split into 2 orders if exists!
        try:
            self._delegate_orders(bill, session_info.cart)
        except Exception:
            # I don't know which error can occur here!
            logger.exception("Failed to delegate orders")
            messages.error(request, "Wystąpił błąd podczas tworzenia zamówienia")
            return redirect("service:cart")

        # change tables status
        self._change_tables_status(session_info.tables)

        messages.success(
            request, f"Zamówienie na rachunek #{bill.pk} zostało ukończone."
        )
        logger.info(f"Bill #{bill.pk} created by waiter {session_info.waiter}")

        clear_session(self.request, ["cart", "tables", "waiter", "bill"])

        return redirect("service:menu-waiter")


def api_remove_from_cart(request, index):
    cart = request.session.get("cart", [])
    if cart:
        del_item = cart.pop(index)
        request.session["cart"] = cart
        request.session.modified = True
        print("Deleted item:", del_item)
    return redirect("service:cart")


def create_order(bill: Bill, items: Iterable[dict], **kwargs):
    if not items:
        return
    order = Order.objects.create(bill=bill, **kwargs)
    # TODO: here we should check is the product is available!
    for item in items:
        payload = {
            "order": order,
            "menu_item_id": item["item_id"],
            "name_snapshot": item["name"],
            "price_snapshot": item["price"],
            "quantity": item["quantity"],
            "note": item["note"],
        }
        order_item = OrderItem.objects.create(**payload)
        for addition in item["additions"]:
            OrderItemAddition.objects.create(
                order_item=order_item,
                addition_id=addition["id"],
                name_snapshot=addition["name"],
                price_snapshot=addition["price"],
            )

    if kwargs["category"] == Location.KITCHEN:
        group_name = "kitchen_orders"
    else:
        group_name = "bar_orders"
    send_payload_to_recipient(order.pk, group_name, bill.service.user.username)


def get_order_details(order_id, sender: str) -> Optional[dict]:
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return None
    # if order.category == Location.BAR:
    #     return

    order_items = []
    for item in order.order_items.order_by("name_snapshot").all():
        order_items.append(
            {
                "id": item.id,
                "name_snapshot": item.full_name_snapshot,
                "quantity": item.quantity,
                "note": item.note,
            }
        )

    return {
        "id": order.id,
        "sender": sender,
        "table": order.bill.str_tables(),
        "status": order.status,
        "order_items": order_items,
        "created_at": timezone.localtime(order.created_at).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }


def send_payload_to_recipient(pk: int, group_name: str, sender: str):
    order_detail = get_order_details(pk, sender)
    if order_detail is None:
        return None
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {"type": "new_order", "order_data": order_detail},
    )


def clear_cart(request):
    clear_session(request, ["cart", "tables", "waiter", "bill"])
    messages.success(request, "Zamówienie zostało anulowane!")

    return redirect("service:menu-waiter")


@require_POST
def close_bill(request, pk):
    payment_method = request.POST.get("payment_method")
    bill = get_object_or_404(Bill, pk=pk)
    if bill.status != StatusBill.OPEN:
        messages.error(request, "Nie można zamknąć, zamkniętego rachunku!")
        return redirect("extend-bill-detail", pk=pk)
    # update fields
    bill.status = StatusBill.CLOSED
    bill.payment_method = PaymentMethod(
        payment_method
    )  # ValueError when somethind, was wrong
    bill.closed_at = timezone.now()
    bill.save(update_fields=["status", "payment_method", "closed_at"])

    bill_tables = bill.table.all()
    for table in bill_tables:
        _number_of_open_bills = Bill.objects.filter(
            Q(table=table) & Q(status=StatusBill.OPEN)
        ).count()
        if _number_of_open_bills == 0:
            table.is_occupied = False
            table.save()
    messages.success(request, f"Rachunek #{bill.pk} został zamknięty.")
    return redirect("service:menu-waiter")


def tables_view(request):
    if request.method == "GET":
        tables = Table.objects.filter(is_active=True)
        waiters = Worker.objects.filter(
            Q(position=Position.WAITER) | Q(position=Position.BARISTA)
        ).values("user__username", "pk")
        return render(
            request, "service/table_order.html", {"tables": tables, "waiters": waiters}
        )

    elif request.method == "POST":
        tables_selected = request.POST.get("tables")
        waiter = request.POST.get("waiter")
        if not tables_selected or not waiter:
            messages.error(
                request,
                "Aby przejść do zamówienia wybierz stolik oraz kelnera który przyjmie zamówienie",
            )
            return redirect("service:order-table")
        if tables_selected:
            tables_list = [int(t.strip()) for t in tables_selected.split(",")]
            request.session["tables"] = tables_list
            request.session["waiter"] = waiter
            print(f"{tables_list = }, {waiter = }")
        return redirect("service:items-waiter")


def table_settle_view(request):
    """
    View for tables where are only tables booking.
    """
    action = request.GET.get("action", "").lower()
    if not action or action not in ["bill", "order"]:
        action = "bill"

    return render(
        request,
        "service/table_settle.html",
        {"tables": Table.objects.filter(is_active=True), "action": action},
    )


def waiter_notification(request):
    return render(request, "service/waiter_notifications.html")


def add_order_to_bill(request, pk: int):
    bill = Bill.objects.get(pk=pk)
    if not bill:
        return HttpResponseNotFound("<h1>Page not found!</h1>")
    request.session["bill"] = pk
    request.session["tables"] = [t.pk for t in bill.table.all()]
    request.session["waiter"] = str(bill.service.pk)
    return redirect("service:items-waiter")


def check_notifications(request):
    has_new = Notification.objects.filter(status=NotificationStatus.WAIT).exists()
    return JsonResponse({"has_new": has_new})
