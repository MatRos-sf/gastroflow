import logging

from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models import Q
from django.utils import translation
from django.utils.translation import gettext as _

from order.models import NotificationStatus, Order, OrderItem
from worker.models import Worker

KITCHEN_GROUP = "kitchen_orders"
BAR_GROUP = "bar_orders"
LOCATION_TO_GROUP = {
    "kitchen": KITCHEN_GROUP,
    "bar": BAR_GROUP,
}

logger = logging.getLogger(__name__)


def create_notification_msg_for_order(
    order: Order, worker: Worker, language: str = settings.LANGUAGE_CODE
) -> str:
    with translation.override(language):
        pending_items = order.order_items.filter(
            Q(notification__isnull=True) | Q(notification__message__isnull=True)
        ).prefetch_related("order_item_additions")

        item_parts = []
        for item in pending_items:
            part = item.name_snapshot
            additions = ", ".join(
                a.name_snapshot for a in item.order_item_additions.all()
            )
            if additions:
                part += f" {_('with')} {additions}"
            if item.note:
                part += f" ({item.note})"
            item_parts.append(part)

        items_str = ", ".join(item_parts)
        return f"{worker.first_name}: {items_str} {_('is ready')} | {order.bill.str_tables()} #{order.pk}"


def create_notification_msg_for_order_item(
    worker: Worker,
    order_item: OrderItem,
    order_id: int,
    language: str = settings.LANGUAGE_CODE,
) -> str:
    with translation.override(language):
        base = f"{worker.first_name}: {order_item.name_snapshot} "
        additions = ",".join(
            addition.name_snapshot for addition in order_item.order_item_additions.all()
        )
        if additions:
            base += f"{_('with')} {additions} "
        note = order_item.note
        if note:
            base += f"({note}) "
        base += f"{_('is ready')} | {order_item.order.bill.str_tables()} #{order_id}"
        return base


def _fetch_and_update_notification(
    order_id: int, item_id: int, language: str = settings.LANGUAGE_CODE
) -> dict | None:
    try:
        order_item = OrderItem.objects.select_related(
            "notification__worker",
            "notification__item__order__bill",
        ).get(id=item_id, order_id=order_id)

        notification = order_item.notification
        notification.message = create_notification_msg_for_order_item(
            notification.worker, notification.item, notification.item.order.pk, language
        )
        notification.status = NotificationStatus.WAITING_TO_READ
        notification.save()

        return {
            "id": notification.id,
            "message": notification.message,
            "notification_type": notification.notification_type,
            "last_update": notification.last_update.isoformat(),
        }
    except OrderItem.DoesNotExist:
        logger.error(f"OrderItem {item_id} not found for order {order_id}.")
        return None


async def dispatch_item_done_notification(
    order_id: int, item_id: int, language: str = settings.LANGUAGE_CODE
) -> None:
    notification_data = await sync_to_async(_fetch_and_update_notification)(
        order_id, item_id, language
    )

    if not notification_data:
        return

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "notifications",
        {"type": "new_notification", **notification_data},
    )
    logger.info(f"Notification for item {item_id} sent to 'notifications' group.")


def _fetch_and_update_order_notification(order_id: int, language: str) -> dict | None:
    try:
        order = Order.objects.select_related(
            "notification__worker",
            "bill__waiter",
        ).get(id=order_id)

        has_pending = order.order_items.filter(
            Q(notification__isnull=True) | Q(notification__message__isnull=True)
        ).exists()

        if not has_pending:
            logger.info(
                f"Order {order_id} has no pending items — skipping order notification."
            )
            return None

        notification = order.notification
        notification.message = create_notification_msg_for_order(
            order, order.bill.waiter, language
        )
        notification.status = NotificationStatus.WAITING_TO_READ
        notification.save()

        return {
            "id": notification.id,
            "message": notification.message,
            "notification_type": notification.notification_type,
            "last_update": notification.last_update.isoformat(),
        }
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found.")
        return None


async def dispatch_order_ready_notification(
    order_id: int, language: str = settings.LANGUAGE_CODE
) -> None:
    notification_data = await sync_to_async(_fetch_and_update_order_notification)(
        order_id, language
    )

    if not notification_data:
        return

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "notifications",
        {"type": "new_notification", **notification_data},
    )
    logger.info(
        f"Order ready notification for order {order_id} sent to 'notifications' group."
    )


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
