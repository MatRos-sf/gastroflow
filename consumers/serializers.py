from datetime import datetime

from django.utils import timezone

from consumers.utils import dish_is_done, get_status_notification
from order.models import Order


def serialize_items_from_order(order: Order) -> list[dict[str, int | str | bool]]:
    items = []
    for item in order.order_items.order_by("name_snapshot").all():
        notification_status = get_status_notification(item)

        items.append(
            {
                "id": item.id,
                "name_snapshot": item.name_snapshot,
                "quantity": item.quantity,
                "note": item.note,
                "is_done": dish_is_done(notification_status),
            }
        )
    return items


def serialize_order(order: Order) -> dict[str, int | str | list | datetime]:
    return {
        "id": order.pk,
        "sender": str(order.bill.waiter),
        "table": order.bill.str_tables(),
        "status": order.status,
        "order_items": serialize_items_from_order(order),
        "created_at": timezone.localtime(order.created_at).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }
