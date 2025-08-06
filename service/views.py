from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render

from menu.models import Addition, Item
from order.models import Bill, Order, OrderItem, OrderItemAddition, StatusBill


def menu_waiter(request):
    return render(request, "service/menu_waiter.html")


def item_list(request):
    if request.method == "POST":
        print("Hello")

    items = Item.objects.filter(is_available=True)
    return render(request, "service/items_waiter.html", {"object_list": items})


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


def do_order(request):
    cart = request.session.get("cart", [])
    print(cart)
    if request.method == "POST":
        print("request.POST")
        if cart:
            print("cart")
            table = request.POST.get("table")
            bill = Bill.objects.create(table=table)
            print(bill)
            # Order
            order = Order.objects.create(bill=bill, status=StatusBill.OPEN)
            for item in cart:
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
            request.session["cart"] = []
            return redirect("service:menu-waiter")


def cart(request):
    cart = request.session.get("cart", [])
    return render(request, "service/cart_waiter.html", {"cart": cart})
