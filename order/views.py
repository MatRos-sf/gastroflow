from datetime import date as date_cls

from django.contrib import messages
from django.db.utils import IntegrityError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView, ListView

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


class BillListView(ListView):
    model = Bill
    template_name = "order/bill_summary_list.html"
    paginate_by = 24  # opcjonalnie

    def get_queryset(self):
        # prefetch: orders -> order_items -> order_item_additions
        return (
            Bill.objects.select_related("service")
            .prefetch_related("table", "orders__order_items__order_item_additions")
            .order_by("-created_at")
        )


class BillDeleteView(DeleteView):
    model = Bill
    template_name = "order/bill_confirm_delete.html"  # nieużywane, bo mamy modal
    success_url = reverse_lazy("summary-bill")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        note = request.POST.get("delete_note", "").strip()
        if note:
            messages.info(request, f"Usunięto Bill #{self.object.pk}. Notatka: {note}")
        else:
            messages.info(request, f"Usunięto Bill #{self.object.pk}.")

        # TODO: check and release tables
        return super().post(request, *args, **kwargs)
