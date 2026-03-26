import json
import logging
from enum import StrEnum

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from consumers.queries import (
    get_available_waiters,
    get_unread_notifications,
    get_unserved_orders,
)
from consumers.services import (
    dispatch_call_waiter_notification,
    dispatch_item_done_notification,
    dispatch_order_ready_notification,
)
from order.models import (
    Location,
    Notification,
    NotificationStatus,
    OrderItem,
    OrderItemStatus,
    StatusOrder,
)
from order.queries import (
    update_batch_notifications_status,
    update_batch_order_items_status,
)

logger = logging.getLogger(__name__)


class ConsumerActionType(StrEnum):
    ORDER_STATUS_UPDATE = "order_status_update"
    ORDER_REMOVE = "order_remove"
    ITEM_REMOVE = "item_remove"
    CHANGE_TABLE = "change_table"
    CALL_WAITER = "call_waiter"
    NEW_ORDER = "new_order"
    NEW_NOTIFICATION = "new_notification"
    READ_NOTIFICATION = "read_notification"
    READ_ALL_NOTIFICATIONS = "read_all_notifications"


class BaseConsumer(AsyncWebsocketConsumer):
    GROUP_NAME: str
    CATEGORY: Location

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

        logger.info(f"Connected to {self.CATEGORY} orders group: {self.GROUP_NAME}")

        orders = await get_unserved_orders(self.CATEGORY)
        waiters = await get_available_waiters()

        await self.send(
            text_data=json.dumps(
                {"type": "initial_orders", "orders": orders, "waiters": waiters}
            )
        )

    async def disconnect(self, close_code):
        logger.info(
            f"Disconnected from {self.CATEGORY} orders group: {self.GROUP_NAME}"
        )
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        handler = getattr(self, f"handle_{action}", self.handle_unknown)
        await handler(data)

    async def order_status_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": ConsumerActionType.ORDER_STATUS_UPDATE,
                    "order_id": event["order_id"],
                    "new_status": event["new_status"],
                }
            )
        )

    async def item_remove(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": ConsumerActionType.ITEM_REMOVE,
                    "item_id": event["item_id"],
                    "order_id": event["order_id"],
                }
            )
        )

    async def order_remove(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": ConsumerActionType.ORDER_REMOVE,
                    "order_id": event["order_id"],
                }
            )
        )

    async def change_table(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": ConsumerActionType.CHANGE_TABLE,
                    "order_id": event["order_id"],
                    "new_table": event["new_table"],
                }
            )
        )

    async def new_order(self, event):
        order_data = event["order_data"]
        await self.send(
            text_data=json.dumps(
                {"type": ConsumerActionType.NEW_ORDER, "order": order_data}
            )
        )

    async def handle_ping(self, data: dict) -> None:
        logger.debug(f"[{self.CATEGORY}] Received ping, connection is active.")

    async def handle_call_waiter(self, data: dict) -> None:
        waiter_name = data.get("first_name")
        waiter_id = data.get("id")

        if not waiter_id or not waiter_name:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "action": "call_waiter",
                        "message": "Missing first_name or id",
                    }
                )
            )
            return

        language = self.scope.get("cookies", {}).get(
            settings.LANGUAGE_COOKIE_NAME, settings.LANGUAGE_CODE
        )
        await dispatch_call_waiter_notification(
            waiter_name, waiter_id, self.CATEGORY.label, language
        )

    async def handle_item_done(self, data: dict):
        order_id = data.get("order_id")
        item_id = data.get("item_id")
        if not item_id or not order_id:
            await self.send(
                json.dumps(
                    {
                        "type": "error",
                        "action": "item_done",
                        "message": "Missing item_id or order_id",
                    }
                )
            )
            return

        await OrderItem.objects.filter(id=item_id).aupdate(status=OrderItemStatus.READY)
        language = self.scope.get("cookies", {}).get(
            settings.LANGUAGE_COOKIE_NAME, settings.LANGUAGE_CODE
        )
        await dispatch_item_done_notification(order_id, item_id, language)

    async def _update_order_status(self, order_id: int, new_status: str) -> None:
        await sync_to_async(update_batch_order_items_status)(order_id, new_status)
        await self.channel_layer.group_send(
            self.GROUP_NAME,
            {
                "type": ConsumerActionType.ORDER_STATUS_UPDATE,
                "order_id": order_id,
                "new_status": new_status,
            },
        )

    async def handle_order_preparing(self, data):
        order_id = data.get("order_id")
        if not order_id:
            await self.send(
                json.dumps(
                    {
                        "type": "error",
                        "action": "preparing",
                        "message": "Missing order_id",
                    }
                )
            )
            return
        await self._update_order_status(order_id, StatusOrder.PREPARING)

    async def handle_order_ready(self, data):
        order_id = data.get("order_id")
        if not order_id:
            await self.send(
                json.dumps(
                    {"type": "error", "action": "ready", "message": "Missing order_id"}
                )
            )
            return
        await self._update_order_status(order_id, StatusOrder.READY)
        language = self.scope.get("cookies", {}).get(
            settings.LANGUAGE_COOKIE_NAME, settings.LANGUAGE_CODE
        )
        await dispatch_order_ready_notification(order_id, language)

    async def handle_unknown(self, data: dict):
        logger.warning(f"Unknown action: {data}")


class BaseNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

        notifications = await get_unread_notifications()

        await self.send(
            text_data=json.dumps(
                {"type": "initial_notifications", "notifications": notifications}
            )
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        handler = getattr(self, f"handle_{action}", self.handle_unknown)
        await handler(data)

    async def new_notification(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": ConsumerActionType.NEW_NOTIFICATION,
                    "id": event["id"],
                    "message": event["message"],
                    "notification_type": event["notification_type"],
                    "last_update": event["last_update"],
                }
            )
        )

    async def read_notification(self, event):
        await self.send(
            text_data=json.dumps(
                {"type": ConsumerActionType.READ_NOTIFICATION, "id": event["id"]}
            )
        )

    async def read_all_notifications(self, event):
        await self.send(
            text_data=json.dumps(
                {"type": ConsumerActionType.READ_ALL_NOTIFICATIONS, "ids": event["ids"]}
            )
        )

    async def handle_unknown(self, data: dict):
        logger.warning(f"Unknown action: {data}")

    async def handle_read_notification(self, data: dict):
        noti_id = data.get("id")
        if not noti_id:
            await self.send(
                json.dumps(
                    {
                        "type": "error",
                        "action": "read_notification",
                        "message": "Missing notification id",
                    }
                )
            )
            return

        try:
            noti = await Notification.objects.aget(id=noti_id)
        except Notification.DoesNotExist:
            await self.send(
                json.dumps(
                    {
                        "type": "error",
                        "action": "read_notification",
                        "message": f"Notification {noti_id} not found",
                    }
                )
            )
            return

        noti.status = NotificationStatus.READ
        await noti.asave()

        await self.channel_layer.group_send(
            self.GROUP_NAME,
            {"type": ConsumerActionType.READ_NOTIFICATION, "id": noti_id},
        )

    async def handle_read_all_notification(self, data: dict):
        noti_ids = data.get("ids")
        if not noti_ids:
            await self.send(
                json.dumps(
                    {
                        "type": "error",
                        "action": "read_all_notification",
                        "message": "Missing id of notifications",
                    }
                )
            )
            return

        await sync_to_async(update_batch_notifications_status)(
            noti_ids, NotificationStatus.READ
        )
        await self.channel_layer.group_send(
            self.GROUP_NAME,
            {"type": ConsumerActionType.READ_ALL_NOTIFICATIONS, "ids": noti_ids},
        )
