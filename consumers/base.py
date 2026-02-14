import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

from consumers.serializers import serialize_order

# from consumers.utils import dish_is_done, get_status_notification
from order.models import (
    Location,
    NotificationStatus,
    Order,
    OrderItem,
    OrderItemStatus,
    StatusOrder,
)
from worker.models import Worker

logger = logging.getLogger(__name__)


class BaseConsumer(AsyncWebsocketConsumer):
    GROUP_NAME: str
    CATEGORY: Location

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

        logger.info(f"Connected to {self.CATEGORY} orders group: {self.GROUP_NAME}")

        orders = await self.get_initial_orders()

        await self.send(
            text_data=json.dumps({"type": "initial_orders", "orders": orders})
        )

    async def disconnect(self, close_code):
        logger.info(
            f"Disconnected from {self.CATEGORY} orders group: {self.GROUP_NAME}"
        )
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        order_id = data.get("order_id")

        if action == "ping":
            logger.debug(f"[{self.CATEGORY}] Received ping, connection is active.")
            return

        elif action == "item_done":
            item_id = data.get("item_id")
            username = data.get("username")
            if item_id and username:
                await self.send_notification(order_id, item_id)

        elif order_id and action:
            new_status = None
            if action == "preparing":
                new_status = StatusOrder.PREPARING
            elif action == "ready":
                new_status = StatusOrder.READY

            if new_status:
                await sync_to_async(self.update_order_status)(order_id, new_status)

                await self.channel_layer.group_send(
                    self.GROUP_NAME,
                    {
                        "type": "order_status_update",
                        "order_id": order_id,
                        "new_status": new_status,
                    },
                )

    def update_order_status(self, order_id, new_status):
        try:
            order = Order.objects.get(id=order_id)
            order.status = new_status

            if new_status == StatusOrder.PREPARING:
                OrderItem.objects.filter(
                    Q(order=order) & Q(status=OrderItemStatus.WAITING)
                ).update(
                    status=OrderItemStatus.PREPARING,
                    started_at=timezone.now(),
                )
                order.preparing_at = timezone.now()
            elif new_status == StatusOrder.READY:
                OrderItem.objects.filter(order=order).update(
                    status=OrderItemStatus.READY,
                    finished_at=timezone.now(),
                )
                OrderItem.objects.filter(order=order, started_at__isnull=True).update(
                    started_at=timezone.now(),
                )
                order.finished_at = timezone.now()

            if new_status == StatusOrder.READY:
                order.readied_at = timezone.now()
            order.save()
            logger.info(f"Order {order_id} status updated to {new_status}")
        except Order.DoesNotExist:
            logger.error(f"Order with ID {order_id} does not exist.")

    async def order_status_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "order_status_update",
                    "order_id": event["order_id"],
                    "new_status": event["new_status"],
                }
            )
        )

    async def new_order(self, event):
        order_data = event["order_data"]
        await self.send(
            text_data=json.dumps({"type": "new_order", "order": order_data})
        )

    @sync_to_async
    def get_initial_orders(self):
        orders = Order.objects.filter(
            status__in=[StatusOrder.ORDER, StatusOrder.PREPARING],
            category=self.CATEGORY,
        ).order_by("created_at")
        return [serialize_order(order) for order in orders]

    @sync_to_async
    def get_notification_data(self, order_id, item_id):
        try:
            order_item = OrderItem.objects.get(id=item_id, order_id=order_id)
            notification = order_item.notification
            if notification.status in [
                NotificationStatus.WAIT,
                NotificationStatus.SERVE,
            ]:
                return None

            notification.status = NotificationStatus.WAIT
            notification.save()

            return {
                "id": notification.id,
                "worker": str(notification.worker),
                "order_item": notification.order_item.full_name_snapshot
                + (
                    f" ({notification.order_item.note})"
                    if notification.order_item.note
                    else ""
                ),
                "table": notification.order_item.order.bill.str_tables(),
                "created_at": notification.last_update.isoformat(),
            }
        except (OrderItem.DoesNotExist, User.DoesNotExist, Worker.DoesNotExist) as e:
            logger.error(f"Error creating notification: {e}")
            return None

    async def send_notification(self, order_id, item_id):
        notification_data = await self.get_notification_data(order_id, item_id)
        if notification_data:
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                "notifications",
                {
                    "type": "new_notification",
                    **notification_data,
                },
            )
            logger.info(
                f"Notification for item {item_id} sent to 'notifications' group."
            )
        else:
            logger.warning(f"Notification already exists for item {item_id}.")
