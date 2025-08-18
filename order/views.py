from datetime import date as date_cls

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .models import Item
from .raport import daily_summary


# Create your views here.
def home(request):
    return HttpResponse("Hello, world. You're at the order home.")


# class OrderMenuView(ListView):
#     model = Item
#     template_name = "order/order_menu.html"


def item_list(request):
    items = Item.objects.all()
    return render(request, "order/order_menu.html", {"object_list": items})


def daily_report(request):
    date_str = request.GET.get("date")
    if date_str:
        try:
            chosen_date = date_cls.fromisoformat(date_str)  # format YYYY-MM-DD
        except ValueError:
            chosen_date = timezone.localdate()
    else:
        chosen_date = timezone.localdate()

    report = daily_summary(chosen_date)

    context = {
        "date": chosen_date,
        "report": report,
    }
    return render(request, "order/raport.html", context)
