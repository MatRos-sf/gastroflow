from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def bar_orders_view(request):
    return render(request, "consumers/bar/orders.html", {"ws_path": "bar/orders"})


@login_required
def kitchen_orders_view(request):
    return render(
        request, "consumers/kitchen/orders.html", {"ws_path": "kitchen/orders"}
    )


@login_required
def notifications_view(request):
    return render(request, "consumers/waiter_notification.html")
