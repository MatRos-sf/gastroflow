from typing import Iterable, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView

from menu.models import Addition, Item, Location, MenuType
from order.models import Bill, Order, OrderItem, OrderItemAddition, StatusBill

from .models import Table


def menu_waiter(request):
    return render(request, "service/menu_waiter.html")


def item_list(request):
    category = request.GET.get("category", MenuType.MAIN)

    items = Item.objects.exclude(menu=MenuType.UNAVAILABLE).filter(menu=category)

    items_no_sub = items.filter(sub_menu__isnull=True)
    items_with_sub = items.exclude(sub_menu__isnull=True)

    sub_menu_groups = {}
    for sub in items_with_sub.values_list("sub_menu", flat=True).distinct():
        sub_menu_groups[sub] = items_with_sub.filter(sub_menu=sub)
    context = {
        "categories": [
            (value, label)
            for value, label in MenuType.choices
            if value != MenuType.UNAVAILABLE
        ],
        "selected_category": category,
        "items_no_sub": items_no_sub,
        "sub_menu_groups": sub_menu_groups,
    }
    return render(request, "service/items_waiter.html", context)


def add_to_cart(request):
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        quantity = int(request.POST.get("quantity", 1))
        note = request.POST.get("note", "")
        additions_ids = request.POST.getlist("additions")
        item = get_object_or_404(Item, pk=item_id)
        additions = Addition.objects.filter(id__in=additions_ids)

        cart = request.session.get("cart", [])
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
                "category": item.preparation_location,
            }
        )
        request.session["cart"] = cart
        request.session.modified = True
    else:
        return HttpResponseNotFound()
    return redirect("service:items-waiter")


def api_remove_from_cart(request, index):
    print(f"Hello {index}")
    cart = request.session.get("cart", [])
    if cart:
        del_item = cart.pop(index)
        request.session["cart"] = cart
        request.session.modified = True
        print("Deleted item:", del_item)
    return redirect("service:cart-waiter")


def create_order(bill: Bill, items: Iterable[dict], **kwargs):
    if not items:
        return
    order = Order.objects.create(bill=bill, **kwargs)
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
    send_payload_to_recipient(order.pk, order.table)


def do_order(request):
    cart = request.session.get("cart", [])
    if request.method == "POST":
        if cart:
            table = request.POST.get("table")
            bill = Bill.objects.create(table=table)
            print(
                f"Saved bill: {bill}, table from db: {Bill.objects.get(pk=bill.pk).table}"
            )
            # split into 2 orders if exists!
            kitchen = filter(lambda data: data["category"] == Location.KITCHEN, cart)
            bar = filter(lambda data: data["category"] == Location.BAR, cart)

            create_order(bill, kitchen, table=table, category=Location.KITCHEN)
            create_order(bill, bar, table=table, category=Location.BAR)
            # Order kitchen
            # order = Order.objects.create(bill=bill, table=table)
            # for item in cart:
            #     payload = {
            #         "order": order,
            #         "menu_item_id": item["item_id"],
            #         "name_snapshot": item["name"],
            #         "price_snapshot": item["price"],
            #         "quantity": item["quantity"],
            #         "note": item["note"],
            #     }
            #     order_item = OrderItem.objects.create(**payload)
            #     for addition in item["additions"]:
            #         OrderItemAddition.objects.create(
            #             order_item=order_item,
            #             addition_id=addition["id"],
            #             name_snapshot=addition["name"],
            #             price_snapshot=addition["price"],
            #         )
            # make_payload_to_kitchen(order.pk, order.table)
            request.session["cart"] = []

            return redirect("service:menu-waiter")


def get_order_details(order_id) -> Optional[dict]:
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return None  # lub raise, zależnie od kontekstu
    if order.preparation_location == Location.BAR:
        return

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
        "table": order.table,
        "status": order.status,
        "order_items": order_items,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def send_payload_to_recipient(pk: int, table: str):
    order_detail = get_order_details(pk)
    if order_detail is None:
        return None

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "kitchen_orders",
        {"type": "new_order", "table": table, "order_data": order_detail},
    )


def cart(request):
    cart = request.session.get("cart", [])
    return render(request, "service/cart_waiter.html", {"cart": cart})


def clear_cart(request):
    if "cart" in request.session:
        del request.session["cart"]
        messages.success(request, "Zamówienie został wyczyszczone")

    if "tables" in request.session:
        tables = request.session.pop("tables")
        messages.success(
            request,
            f"Stoliki {', '.join(str(table) for table in tables)} zostały wyczyszczone",
        )

    return redirect("service:menu-waiter")


class BillListView(ListView):
    model = Bill
    template_name = "service/bill_list.html"

    def get_queryset(self):
        return Bill.objects.filter(status=StatusBill.OPEN)


class BillDetailView(DetailView):
    model = Bill
    template_name = "service/bill_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = self.object.bill_summary_view()
        return context


def close_bill(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    bill.status = StatusBill.CLOSED
    bill.closed_at = timezone.now()
    bill.save()
    # add message
    return redirect("service:bill")


def tables_view(request):
    if request.method == "GET":
        tables = Table.objects.filter(is_active=True)
    elif request.method == "POST":
        tables_selected = request.POST.get("tables")
        if not tables_selected:
            messages.error(request, "Aby przejść do zamówienia wybierz stolik")
            return redirect("service:order-table")
        if tables_selected:
            tables_list = [int(t.strip()) for t in tables_selected.split(",")]
            request.session["tables"] = tables_list
            print(tables_list)
        return redirect("service:items-waiter")
    return render(request, "service/table_order.html", {"tables": tables})
