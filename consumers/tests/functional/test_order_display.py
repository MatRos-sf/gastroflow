from channels import layers as _channel_layers_module
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase, override_settings
from model_bakery import baker

from consumers.base import ConsumerActionType
from consumers.tests._helpers import TestKitchenConsumer
from menu.models import Location
from order.models import StatusOrder

_IN_MEMORY_LAYER = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


@override_settings(CHANNEL_LAYERS=_IN_MEMORY_LAYER)
class OrderDisplayFunctionalTest(TransactionTestCase):
    def setUp(self):
        _channel_layers_module.channel_layers.backends = {}
        worker = baker.make("worker.Worker", first_name="Anna", last_name="Nowak")
        bill = baker.make("order.Bill", waiter=worker)
        table = baker.make("service.Table", name="T3")
        bill.table.add(table)
        self.order = baker.make(
            "order.Order",
            bill=bill,
            status=StatusOrder.ORDER,
            category=Location.KITCHEN,
        )

    def _communicator(self):
        return WebsocketCommunicator(TestKitchenConsumer.as_asgi(), "/ws/test/")

    async def test_connect_receives_current_orders(self):
        communicator = self._communicator()
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        message = await communicator.receive_json_from()

        self.assertEqual(message["type"], "initial_orders")
        self.assertEqual(len(message["orders"]), 1)
        self.assertEqual(message["orders"][0]["id"], self.order.id)

        await communicator.disconnect()

    async def test_change_table_is_pushed_to_connected_client(self):
        communicator = self._communicator()
        await communicator.connect()
        await communicator.receive_json_from()  # consume initial_orders

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            TestKitchenConsumer.GROUP_NAME,
            {
                "type": ConsumerActionType.CHANGE_TABLE,
                "order_id": self.order.id,
                "new_table": "T5",
            },
        )

        message = await communicator.receive_json_from()

        self.assertEqual(message["type"], ConsumerActionType.CHANGE_TABLE)
        self.assertEqual(message["order_id"], self.order.id)
        self.assertEqual(message["new_table"], "T5")

        await communicator.disconnect()
