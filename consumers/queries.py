from asgiref.sync import sync_to_async
from django.db.models import Prefetch

from consumers.serializers import serialize_order
from menu.models import Location
from order.models import Order, OrderItem, StatusOrder


def _get_unserved_orders(category: Location) -> list[dict]:
    """Fetch all unserved orders for the given location"""
    items_qs = OrderItem.objects.prefetch_related("order_item_additions").order_by(
        "name_snapshot"
    )

    qs = (
        Order.objects.filter(
            status__in=[StatusOrder.ORDER, StatusOrder.PREPARING],
            category=category,
        )
        .select_related("bill", "bill__waiter")
        .prefetch_related(
            "bill__table",
            Prefetch("order_items", queryset=items_qs, to_attr="_prefetched_items"),
        )
        .order_by("created_at")
    )

    return [serialize_order(order) for order in qs]


get_unserved_orders = sync_to_async(_get_unserved_orders)
