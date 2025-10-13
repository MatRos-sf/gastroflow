from django.shortcuts import render


def bar_orders(request):
    return render(request, "bar/orders.html")
