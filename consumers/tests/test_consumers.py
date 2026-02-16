from unittest.mock import AsyncMock, patch

from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase

from consumers.base import BaseConsumer


class TestKitchenConsumer(BaseConsumer):
    GROUP_NAME = "test_kitchen_orders"
    CATEGORY = "kitchen"


class ConsumerTestCase(TransactionTestCase):
    def _create_connection(self):
        return WebsocketCommunicator(TestKitchenConsumer.as_asgi(), "/ws/test/")

    @patch("consumers.base.get_unserved_orders", new_callable=AsyncMock)
    async def test_consumer_connect(self, mock_get_unserved_orders):
        """Test WebSocket connection"""
        mock_get_unserved_orders.return_value = [{"id": 1, "status": "pending"}]
        communicator = self._create_connection()

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        response = await communicator.receive_json_from()

        self.assertEqual(response["type"], "initial_orders")
        mock_get_unserved_orders.assert_awaited_once()
        await communicator.disconnect()
