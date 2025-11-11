from datetime import datetime
from pprint import pprint

from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F

from menu.models import MenuType
from order.models import Location, Order


def generate_summary_report(
    from_date: datetime, to_date: datetime, calculator_collection: list
):
    data = {}
    start, end = from_date, to_date
    for calc in calculator_collection:
        data[calc.name] = calc.calculate(start, end)
    data["date_from"] = from_date.isoformat()
    data["date_to"] = to_date.isoformat()
    pprint(data)

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

    data["kitchen_metrics"] = {
        "avg_prep_time": avg_prep,
    }

    return data
