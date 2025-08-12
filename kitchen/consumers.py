import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from order.models import Location, Order, StatusOrder


class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Obsługuje połączenie klienta WebSocket.
        Dołącza klienta do grupy "kitchen_orders" i wysyła początkową listę zamówień.
        """
        self.kitchen_group_name = "kitchen_orders"

        # Dołączenie do grupy
        await self.channel_layer.group_add(self.kitchen_group_name, self.channel_name)
        await self.accept()

        print(f"Connected to kitchen orders group: {self.kitchen_group_name}")

        # Pobieranie i wysyłanie istniejących zamówień
        orders = await self.get_initial_orders()
        await self.send(
            text_data=json.dumps({"type": "initial_orders", "orders": orders})
        )

    async def disconnect(self, close_code):
        """
        Obsługuje rozłączenie klienta WebSocket.
        Usuwa klienta z grupy.
        """
        print(f"Disconnected from kitchen orders group: {self.kitchen_group_name}")
        await self.channel_layer.group_discard(
            self.kitchen_group_name, self.channel_name
        )

    async def receive(self, text_data):
        """
        Obsługuje wiadomości wysyłane przez klienta (przez JavaScript).
        Zmienia status zamówienia w bazie danych i wysyła powiadomienie do grupy.
        """
        print("Received message from client:", text_data)
        data = json.loads(text_data)
        action = data.get("action")
        order_id = data.get("order_id")

        if order_id and action:
            new_status = None
            if action == "preparing":
                new_status = StatusOrder.PREPARING
            elif action == "ready":
                new_status = StatusOrder.READY

            if new_status:
                # Wywołanie synchronicznej metody do operacji na bazie danych
                await sync_to_async(self.update_order_status)(order_id, new_status)

                # Wysyłanie powiadomienia do całej grupy, że status został zmieniony
                await self.channel_layer.group_send(
                    self.kitchen_group_name,
                    {
                        "type": "order_status_update",
                        "order_id": order_id,
                        "new_status": new_status,
                    },
                )

    def update_order_status(self, order_id, new_status):
        """
        Synchroniczna metoda do aktualizacji statusu zamówienia w bazie danych.
        Jest wywoływana przez `sync_to_async`, aby nie blokować głównego wątku.
        """
        try:
            order = Order.objects.get(id=order_id)
            order.status = new_status
            if new_status == StatusOrder.READY:
                order.readied_at = timezone.now()
            order.save()
            print(f"Order {order_id} status updated to {new_status}")
        except Order.DoesNotExist:
            print(f"Error: Order with ID {order_id} does not exist.")

    async def order_status_update(self, event):
        """
        Obsługuje wiadomości z grupy dotyczące zmian statusu zamówienia.
        Wysyła wiadomość do klienta, aby zaktualizować interfejs.
        """
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
        """
        Obsługuje wiadomości z grupy dotyczące nowych zamówień.
        Wysyła wiadomość do klienta, aby dodać nowe zamówienie do widoku.
        """
        print("Sending new order to client:", event["order_data"])
        order_data = event["order_data"]
        await self.send(
            text_data=json.dumps({"type": "new_order", "order": order_data})
        )

    @sync_to_async
    def get_initial_orders(self):
        """
        Synchroniczna metoda do pobierania początkowych zamówień z bazy danych.
        Jest wywoływana przez `sync_to_async`.
        """
        orders = Order.objects.filter(
            status__in=[StatusOrder.ORDER, StatusOrder.PREPARING],
            category=Location.KITCHEN,
        ).order_by("-created_at")
        orders_list = []
        for order in orders:
            order_items = []
            for item in order.order_items.order_by("name_snapshot").all():
                order_items.append(
                    {
                        "id": item.id,
                        "name_snapshot": item.full_name_snapshot,
                        "quantity": item.quantity,
                        "note": item.note,
                    }
                )

            # for item in order.order_items.all():
            #     order_items.append(
            #         {
            #             "id": item.id,
            #             "name_snapshot": item.name_snapshot,
            #             "quantity": item.quantity,
            #             "note": item.note,
            #         }
            #     )

            orders_list.append(
                {
                    "id": order.id,
                    "table": None,
                    "status": order.status,
                    "order_items": order_items,
                    "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return orders_list
