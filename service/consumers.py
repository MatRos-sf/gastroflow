import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from order.models import Notification, NotificationStatus


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.notification_group_name = "notifications"
        await self.channel_layer.group_add(
            self.notification_group_name, self.channel_name
        )
        await self.accept()

        notifications = await self.get_initial_notifications()
        await self.send(
            text_data=json.dumps(
                {"type": "initial_notifications", "notifications": notifications}
            )
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.notification_group_name, self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "ping":
            print("[WAITER] Received ping, connection is active.")
            return

        if data.get("action") == "notification_seen" and data.get("notification_id"):
            await sync_to_async(self.mark_notification_seen)(data["notification_id"])
            await self.channel_layer.group_send(
                self.notification_group_name,
                {
                    "type": "notification_update",
                    "notification_id": data["notification_id"],
                },
            )

    def mark_notification_seen(self, notification_id):
        try:
            n = Notification.objects.get(id=notification_id)
            n.status = NotificationStatus.SERVE
            n.save()
        except Notification.DoesNotExist:
            print(f"Notification {notification_id} not found.")

    async def notification_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification_seen",
                    "notification_id": event["notification_id"],
                }
            )
        )

    async def new_notification(self, event):
        await self.send(text_data=json.dumps({"type": "new_notification", **event}))

    @sync_to_async
    def get_initial_notifications(self):
        qs = Notification.objects.filter(status=NotificationStatus.WAIT).order_by(
            "last_update"
        )
        return [
            {
                "id": n.id,
                "worker": str(n.worker),
                "order_item": n.order_item.name_snapshot,
                "table": n.order_item.order.bill.str_tables(),
                "last_update": n.last_update.isoformat(),
            }
            for n in qs
        ]
