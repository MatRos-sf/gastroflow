__all__ = ["get_order_items_summary"]
import datetime
from typing import Any

from django.db.models import Sum

from order.models import OrderItem


def get_order_items_summary(
    from_date: datetime.datetime, to_date: datetime.datetime
) -> list[dict[str, Any]]:
    items = (
        OrderItem.objects.filter(created_at__range=(from_date, to_date))
        .values("name_snapshot")
        .annotate(quantity=Sum("quantity"), line_final_total=Sum("line_final_total"))
        .order_by("-line_final_total")
    )

    return items
