from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def bar_orders_view(request):
    return render(request, "consumers/bar/orders.html")


@login_required
def kitchen_orders_view(request):
    return render(request, "consumers/kitchen/orders.html")
