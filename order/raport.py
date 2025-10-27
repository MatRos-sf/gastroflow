# import datetime
from datetime import datetime
from decimal import Decimal
from typing import Optional

from django.db.models import (  # Value,
    Avg,
    Case,
    Count,
    DurationField,
    ExpressionWrapper,
    F,
    IntegerField,
    Sum,
    When,
)
from django.db.models.functions import Coalesce

from menu.models import MenuType
from order.models import Bill, Location, Order, OrderItem, PaymentMethod, StatusBill

# from django.utils import timezone


class ReportCalculator:
    """Base class for report calculators."""

    name = "bill_status"

    def calculate(self, from_date, to_date):
        raise NotImplementedError("This method should be implemented by subclasses")


class CountBillStatus(ReportCalculator):
    """Calculates the number of bills with each status between two dates."""

    name = "CountBillStatus"

    def calculate(self, from_date, to_date):
        return Bill.objects.filter(created_at__range=(from_date, to_date)).aggregate(
            opened=Count(
                Case(When(status=StatusBill.OPEN, then=1), output_field=IntegerField())
            ),
            closed=Count(
                Case(
                    When(status=StatusBill.CLOSED, then=1), output_field=IntegerField()
                )
            ),
        )


# def day_bounds_local(from_date, to_date):
#     """
#     Zwraca [start, end] dla danego dnia w bieżącej strefie czasowej (zoneinfo).
#     """
#     tz = timezone.get_current_timezone()
#     start = datetime.combine(from_date, time.min).replace(tzinfo=tz)
#     if to_date:
#         end = datetime.combine(to_date, time.max).replace(tzinfo=tz)
#     else:
#         end = datetime.combine(from_date, time.max).replace(tzinfo=tz)
#     return start, end


def summary_report():
    pass


def daily_summary(from_date=datetime.date, to_date: Optional[datetime.date] = None):
    """
    Główny raport dzienny. Zwraca słownik z KPI.
    Domyślnie: dzisiaj (wg Europe/Warsaw).
    """

    # start, end = day_bounds_local(from_date, to_date)
    start, end = from_date, to_date
    print("Daily summary")
    print(start, end)
    # 1) Rachunki otwarte/zamknięte tego dnia
    bills_opened = Bill.objects.filter(created_at__range=(start, end)).count()
    bills_closed = Bill.objects.filter(
        status=StatusBill.CLOSED, closed_at__range=(start, end)
    ).count()

    # 2) Zakres itemów przypisujemy do dnia OTWARCIA rachunku.
    #    Jeśli wolisz dzień ZAMKNIĘCIA, użyj order__bill__closed_at__range=(start, end).
    items_qs = OrderItem.objects.filter(
        order__bill__created_at__range=(start, end)
    ).select_related(
        "order"
    )  # mniej zapytań

    # 3) Łączna sprzedaż (sumujemy quantity)
    items_sold = items_qs.aggregate(total=Coalesce(Sum("quantity"), 0))["total"]

    # 4) Kuchnia vs. Bar (po polu category na Order)
    by_category = (
        items_qs.values("order__category")
        .annotate(sold=Coalesce(Sum("quantity"), 0))
        .order_by()
    )
    # Zamieniamy na prosty słownik typu {'kitchen': x, 'bar': y, ...}
    items_by_category = {row["order__category"]: row["sold"] for row in by_category}

    # 5) Średni czas przygotowania (tylko tam, gdzie mamy oba timestampy)
    # prep_delta = ExpressionWrapper(
    #     F("finished_at") - F("created_at"),
    #     output_field=DurationField(),
    # )
    # avg_prep = items_qs.filter(
    #     started_at__isnull=False, finished_at__isnull=False
    # ).aggregate(avg=Avg(prep_delta))["avg"]
    orders_qs = (
        Order.objects.filter(
            category=Location.KITCHEN,
            created_at__range=(start, end),
            preparing_at__isnull=False,
            readied_at__isnull=False,
        )
    ).exclude(order_items__menu_item__menu=MenuType.OTHER)

    prep_delta = ExpressionWrapper(
        F("readied_at") - F("created_at"),
        output_field=DurationField(),
    )

    avg_prep = orders_qs.aggregate(
        avg=Avg(prep_delta),
        count=Count("id"),
    )["avg"]
    # 6) revenue
    revenue = Decimal("0.00")
    revenue_cash = Decimal("0.00")
    revenue_card = Decimal("0.00")

    daily_bills = Bill.objects.filter(created_at__range=(start, end)).prefetch_related(
        "orders__order_items__order_item_additions"
    )
    for bill in daily_bills:
        summary = bill.bill_summary_view()
        total = summary["total"]
        discount = summary["cost_discount"]
        print(total, discount, bill.payment_method)
        revenue += total - discount
        if bill.payment_method == PaymentMethod.CASH:
            revenue_cash += total - discount
        elif bill.payment_method == PaymentMethod.CARD:
            revenue_card += total - discount

    return {
        "date": from_date.isoformat(),
        "bills": {
            "opened": bills_opened,
            "closed": bills_closed,
        },
        "items": {
            "total_sold": items_sold,
            "by_category": items_by_category,
        },
        "kitchen_metrics": {
            "avg_prep_time": avg_prep,  # timedelta lub None
        },
        "revenue": revenue,
        "revenue_cash": revenue_cash,
        "revenue_card": revenue_card,
    }
