from datetime import datetime

from django.utils import timezone

from order.models import Order


def serialize_additions_from_order_item(item):
    return [
        {"name_snapshot": addition.name_snapshot, "quantity": addition.quantity}
        for addition in item
    ]


def serialize_items_from_order(order: Order) -> list[dict[str, int | str]]:
    items = []
    source = getattr(order, "_prefetched_items", None)
    if source is None:
        source = order.order_items.order_by("name_snapshot").all()
    for item in source:
        items.append(
            {
                "id": item.id,
                "name_snapshot": item.name_snapshot,
                "quantity": item.quantity,
                "note": item.note,
                "status": item.status,
                "additions": serialize_additions_from_order_item(
                    item.order_item_additions.all()
                ),
            }
        )
    return items


def serialize_order(order: Order) -> dict[str, int | str | list | datetime]:
    return {
        "id": order.pk,
        "sender": str(order.bill.waiter),
        "table": order.bill.str_tables(),
        "note": order.bill.note,
        "status": order.status,
        "order_items": serialize_items_from_order(order),
        "created_at": timezone.localtime(order.created_at).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }
