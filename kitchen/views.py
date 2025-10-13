from django.shortcuts import render


def kitchen_orders_view(request):
    return render(request, "kitchen/orders.html")
