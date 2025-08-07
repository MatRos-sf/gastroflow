from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Addition, Item


# Create your views here.
def home(request):
    return HttpResponse("Hello, world. You're at the order home.")


# class OrderMenuView(ListView):
#     model = Item
#     template_name = "order/order_menu.html"


def item_list(request):
    items = Item.objects.filter(is_available=True)
    return render(request, "order/order_menu.html", {"object_list": items})


def add_to_cart(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    quantity = int(request.POST.get("quantity", 1))
    note = request.POST.get("note", "")
    additions_ids = request.POST.getlist("additions")
    additions = Addition.objects.filter(id__in=additions_ids)

    cart = request.session.get("cart", [])

    cart_item = {
        "item_id": item.id,
        "name": item.name,
        "price": str(item.price),
        "quantity": quantity,
        "note": note,
        "additions": [
            {"id": add.id, "name": add.name, "price": str(add.price)}
            for add in additions
        ],
    }

    cart.append(cart_item)
    request.session["cart"] = cart
    request.session.modified = True
    return redirect("item-list")
