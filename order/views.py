import datetime
import logging
import os
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.utils import IntegrityError
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView, DetailView, ListView, View
from django_filters.views import FilterView

from consumers.services import broadcast_item_remove
from menu.models import Location
from model_utils import get_order_additions_summary, get_order_items_summary
from tools.converter import convert_date_from_str_to_date
from tools.raport_calculator import CALCULATOR_COLLECTION

from .filters import OrderFilter
from .forms import DateForm
from .models import (
    Bill,
    Item,
    Order,
    OrderItem,
    OrderItemStatus,
    PaymentMethod,
    StatusBill,
)
from .raport import generate_summary_report
from .tasks import generate_report_and_send_email_task

logger = logging.getLogger(__name__)


def pin_required(view_func):
    def wrapper(request, *args, **kwargs):
        pin = os.getenv("PIN")
        if request.method == "POST":
            provided_pin = request.POST.get("pin")
            if provided_pin == pin:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "Niepoprawny PIN!")
                return redirect("service:menu-waiter")
        return render(request, "order/pin_form.html")

    return wrapper


def item_list(request):
    items = Item.objects.all()
    return render(request, "order/order_menu.html", {"object_list": items})


class ReportView(View):
    calculator_collection = CALCULATOR_COLLECTION
    template_name = "order/raport.html"

    def _parse_dates(
        self, from_d: str | None = None, to_d: str | None = None
    ) -> tuple[datetime.datetime, datetime.datetime]:
        raw_from = self.request.GET.get("from")
        raw_to = self.request.GET.get("to")

        from_date = convert_date_from_str_to_date(
            raw_from or timezone.now().date().strftime("%Y-%m-%d")
        )
        to_date = convert_date_from_str_to_date(raw_to or raw_from, False)

        return from_date, to_date

    def _build_context(
        self, from_date: datetime.datetime, to_date: datetime.datetime
    ) -> dict[str, Any]:
        return {
            "date_from": from_date,
            "date_to": to_date,
            "report": generate_summary_report(
                from_date, to_date, self.calculator_collection
            ),
            "table_report_items": get_order_items_summary(from_date, to_date),
            "table_report_additions": get_order_additions_summary(from_date, to_date),
        }

    def get(self, request):
        raw_from_date = request.GET.get("from", None)
        raw_to_date = request.GET.get("to", None)

        from_date, to_date = self._parse_dates(raw_from_date, raw_to_date)

        return render(
            request, self.template_name, self._build_context(from_date, to_date)
        )


def generate_report(request, from_to):
    # if not request.user.is_staff:
    #     return HttpResponseForbidden("Insufficient permissions")

    try:
        from_date, to_date = from_to.split("_")
        generate_report_and_send_email_task.delay(from_date, to_date)
        messages.success(request, "Raport jest generowany. Zostanie wysłany na email.")
        return redirect("report-selection")
    except ValueError:
        messages.error(request, "Nieprawidłowy format daty")
        return redirect("report-selection")


# TODO: what happened if pk doesn't exists or is wrong
@require_POST
def update_discount(request, pk: int):
    """
    Upgrade discount field
    """
    try:
        bill = get_object_or_404(Bill, pk=pk)
        bill.add_discount(int(request.POST.get("discount")))
    except IntegrityError:
        messages.add_message(
            request, messages.ERROR, "Można dodać tylko zniżki od 0% - 100%"
        )
    except Http404:
        messages.add_message(request, messages.ERROR, "Bill doesn't exists")
    return redirect("extend-bill-detail", pk=pk)


# TODO: BillListView and OpenBillListView look the same
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


class OpenBillListView(ListView):
    model = Bill
    template_name = "service/bill_list.html"

    def get_queryset(self):
        queryset = Bill.objects.filter(status=StatusBill.OPEN)
        table_pk = self.request.GET.get("table")
        if table_pk:
            queryset = queryset.filter(table__pk=table_pk)
        return queryset

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        action = self.request.GET.get("action", "").lower()
        if not action or action not in ["bill", "order"]:
            data["action"] = "bill"
        else:
            data["action"] = action
        return data


# TODO: BillDetailView and ExtendBillDetailView look the same, it should be refactored
class BillDetailView(DetailView):
    model = Bill
    template_name = "order/bill_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = context["object"]
        order_items = obj.orders.prefetch_related("order_items__order_item_additions")
        items = []
        for order in order_items:
            for order_item in order.order_items.all():
                name = order_item.full_name_snapshot
                if order_item.note:
                    name += f" ({order_item.note})"
                items.append(
                    {
                        "pk": order_item.pk,
                        "name": name,
                        "quantity": order_item.quantity,
                    }
                )

        context["items"] = items
        return context


class ExtendBillDetailView(DetailView):
    model = Bill
    template_name = "service/bill_detail.html"
    extra_context = {"payment_methods": PaymentMethod}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payoff = self.object.bill_summary_view()
        context["summary"] = payoff["summary"]
        context["total"] = payoff["total"]
        context["cost_discount"] = payoff["cost_discount"]
        context["discount"] = self.object.discount
        context["total_with_discount"] = payoff["total"] - payoff["cost_discount"]
        return context


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


@require_POST
def close_bill(request, pk):
    payment_method = request.POST.get("payment_method")
    bill = get_object_or_404(Bill, pk=pk)
    if bill.status != StatusBill.OPEN:
        messages.error(request, "Nie można zamknąć, zamkniętego rachunku!")
        return redirect("extend-bill-detail", pk=pk)
    # update fields
    bill.status = StatusBill.CLOSED
    bill.payment_method = PaymentMethod(
        payment_method
    )  # ValueError when somethind, was wrong
    bill.closed_at = timezone.now()
    bill.save(update_fields=["status", "payment_method", "closed_at"])

    bill_tables = bill.table.all()
    for table in bill_tables:
        _number_of_open_bills = Bill.objects.filter(
            Q(table=table) & Q(status=StatusBill.OPEN)
        ).count()
        if _number_of_open_bills == 0:
            table.is_occupied = False
            table.save()
    messages.success(request, f"Rachunek #{bill.pk} został zamknięty.")
    return redirect("service:menu-waiter")


def delete_order_item(request: HttpRequest, pk_order: int, pk_item: int):
    object_item = OrderItem.objects.get(pk=pk_item)
    object_name = object_item.full_name_snapshot
    object_location = object_item.menu_item.preparation_location
    object_item.delete()
    messages.success(request, f"Usunięto {object_name}.")
    broadcast_item_remove(pk_order, pk_item, object_location)
    return redirect("bill-detail", pk=pk_order)


class ReadyOrderListView(LoginRequiredMixin, FilterView):
    """Basic view show previous preparing orders"""

    model = Order
    template_name = "order/order_ready_history.html"
    context_object_name = "items"
    filterset_class = OrderFilter
    paginate_by = 20

    def get_queryset(self):
        qs = (
            Order.objects.select_related("bill")
            .prefetch_related("order_items", "order_items__order_item_additions")
            .filter(status=OrderItemStatus.READY)
            .order_by("-created_at")
        )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Location.values
        ctx["today"] = timezone.localdate().strftime("%Y-%m-%d")
        return ctx


class ReportSelectionView(View):
    """View for handling report generation form submission and redirection.

    This view provides a form for users to select date ranges for report generation.
    It handles both GET requests (displaying the form) and POST requests (processing the form).

    Attributes:
        FORM (DateForm): The form class used for date selection

    Methods:
        get: Renders the report form
        post: Processes the form submission and redirects to the appropriate report view
    """

    FORM = DateForm

    def get(self, request):
        return render(request, "order/report/report_form.html", {"form": self.FORM()})

    def post(self, request):
        form = self.FORM(request.POST)
        if not form.is_valid():
            return render(request, "order/report/report_form.html", {"form": form})

        if "today" in request.POST:
            date_from = timezone.now().date()
            date_to = None
        else:
            cleaned_data = form.cleaned_data
            date_from = cleaned_data.get("from_date")
            date_to = cleaned_data.get("to_date")
        logger.info(f"Date from: {date_from}, Date to: {date_to}")

        url_parameters = (
            f"from={date_from}&to={date_to}" if date_to else f"from={date_from}"
        )

        return redirect(reverse("report") + "?" + url_parameters)
