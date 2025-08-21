from datetime import date as date_cls

from django.contrib import messages
from django.db.utils import IntegrityError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Bill, Item
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


# TODO: what happened if pk doesn't exists or is wrong
@require_POST
def update_discount(request, pk: int):
    """
    Upgrade discount field
    """
    try:
        bill = get_object_or_404(Bill, pk=pk)
        bill.discount = int(request.POST.get("discount"))
        bill.save(update_fields=["discount"])
    except IntegrityError:
        messages.add_message(
            request, messages.ERROR, "Można dodać tylko zniżki od 0% - 100%"
        )
    except Http404:
        messages.add_message(request, messages.ERROR, "Bill doesn't exists")
    return redirect("service:bill-detail", pk=pk)
