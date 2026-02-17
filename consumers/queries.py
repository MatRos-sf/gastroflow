from asgiref.sync import sync_to_async

from consumers.serializers import serialize_order
from menu.models import Location
from order.models import Order, StatusOrder


@sync_to_async
def get_unserved_orders(category: Location):
    """Capture map orders with unserved dishes"""

    qs = Order.objects.filter(
        status__in=[StatusOrder.ORDER, StatusOrder.PREPARING],
        category=category,
    ).order_by("created_at")

    return [serialize_order(order) for order in qs]
