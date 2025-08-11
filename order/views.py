from django.http import HttpResponse
from django.shortcuts import render

from .models import Item


# Create your views here.
def home(request):
    return HttpResponse("Hello, world. You're at the order home.")


# class OrderMenuView(ListView):
#     model = Item
#     template_name = "order/order_menu.html"


def item_list(request):
    items = Item.objects.all()
    return render(request, "order/order_menu.html", {"object_list": items})
