from asgiref.sync import sync_to_async
from django.db.models import Prefetch
from django.utils import timezone

from consumers.serializers import serialize_order
from menu.models import Location
from order.models import Notification, NotificationStatus, Order, OrderItem, StatusOrder
from worker.models import Worker


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


def _get_unread_notifications():
    """Fetch unread notifications"""
    qs = Notification.objects.filter(
        status=NotificationStatus.WAITING_TO_READ
    ).order_by("last_update")
    return [
        {
            "id": noti.id,
            "message": noti.message,
            "notification_type": noti.notification_type,
            "last_update": noti.last_update.isoformat(),
        }
        for noti in qs
    ]


def _get_available_waiters() -> list[dict]:
    today = timezone.now().date()
    return list(
        Worker.objects.filter(
            worktime__start_time__date=today,
            worktime__finish_time__isnull=True,
        )
        .distinct()
        .values("id", "first_name", "last_name")
    )


get_unserved_orders = sync_to_async(_get_unserved_orders)
get_unread_notifications = sync_to_async(_get_unread_notifications)
get_available_waiters = sync_to_async(_get_available_waiters)
