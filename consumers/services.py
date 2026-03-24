import logging

from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer

from order.models import NotificationStatus, OrderItem

KITCHEN_GROUP = "kitchen_orders"
BAR_GROUP = "bar_orders"
LOCATION_TO_GROUP = {
    "kitchen": KITCHEN_GROUP,
    "bar": BAR_GROUP,
}

logger = logging.getLogger(__name__)


def _fetch_and_update_notification(order_id: int, item_id: int) -> dict | None:
    try:
        order_item = OrderItem.objects.get(id=item_id, order_id=order_id)
        notification = order_item.notification

        notification.status = NotificationStatus.WAITING_TO_READ
        notification.save()

        return {
            "id": notification.id,
            "worker": str(notification.worker),
            "order_item": str(notification.item.pk)
            + (f" ({notification.item.note})" if notification.item.note else ""),
            "table": notification.item.order.bill.str_tables(),
            "created_at": notification.last_update.isoformat(),
        }
    except OrderItem.DoesNotExist:
        logger.error(f"OrderItem {item_id} not found for order {order_id}.")
        return None


async def dispatch_item_done_notification(order_id: int, item_id: int) -> None:
    notification_data = await sync_to_async(_fetch_and_update_notification)(
        order_id, item_id
    )

    if not notification_data:
        return

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "notifications",
        {"type": "new_notification", **notification_data},
    )
    logger.info(f"Notification for item {item_id} sent to 'notifications' group.")


def broadcast_item_remove(order_id: int, item_id: int, location: str) -> None:
    group = LOCATION_TO_GROUP.get(location)
    if not group:
        logger.warning(f"Unknown location '{location}' for item_remove broadcast.")
        return
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {"type": "item_remove", "order_id": order_id, "item_id": item_id},
    )


def broadcast_order_remove(order_id: int) -> None:
    channel_layer = get_channel_layer()
    for group in (KITCHEN_GROUP, BAR_GROUP):
        async_to_sync(channel_layer.group_send)(
            group,
            {"type": "order_remove", "order_id": order_id},
        )


def broadcast_change_table(order_id: int, new_table: str) -> None:
    channel_layer = get_channel_layer()
    for group in (KITCHEN_GROUP, BAR_GROUP):
        async_to_sync(channel_layer.group_send)(
            group,
            {"type": "change_table", "order_id": order_id, "new_table": new_table},
        )
