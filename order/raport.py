# reports/services.py
from datetime import datetime, time
from decimal import Decimal

from django.db.models import (
    Avg,
    DecimalField,
    DurationField,
    ExpressionWrapper,
    F,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from order.models import Bill, OrderItem, StatusBill


def day_bounds_local(date):
    """
    Zwraca [start, end] dla danego dnia w bieżącej strefie czasowej (zoneinfo).
    """
    tz = timezone.get_current_timezone()
    start = datetime.combine(date, time.min).replace(tzinfo=tz)
    end = datetime.combine(date, time.max).replace(tzinfo=tz)
    return start, end


def daily_summary(date=None):
    """
    Główny raport dzienny. Zwraca słownik z KPI.
    Domyślnie: dzisiaj (wg Europe/Warsaw).
    """
    if date is None:
        date = timezone.localdate()

    start, end = day_bounds_local(date)

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
    prep_delta = ExpressionWrapper(
        F("finished_at") - F("started_at"),
        output_field=DurationField(),
    )
    avg_prep = items_qs.filter(
        started_at__isnull=False, finished_at__isnull=False
    ).aggregate(avg=Avg(prep_delta))["avg"]

    # 6) Przychód dnia z cen snapshot
    #    Najpierw suma dodatków per item, potem cena pozycji: (price_snapshot * quantity) + additions_total
    items_with_add = items_qs.annotate(
        additions_total=Coalesce(Sum("order_item_additions__price_snapshot"), Value(0))
    ).annotate(
        line_revenue=ExpressionWrapper(
            F("price_snapshot") * F("quantity") + F("additions_total"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    )

    revenue = items_with_add.aggregate(
        total=Coalesce(Sum("line_revenue"), Value(Decimal("0.00")))
    )["total"]

    return {
        "date": date.isoformat(),
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
    }
