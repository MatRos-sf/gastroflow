from django.shortcuts import render


def bar_orders_view(request):
    return render(request, "consumers/bar/orders.html")


def kitchen_orders_view(request):
    return render(request, "consumers/kitchen/orders.html")
