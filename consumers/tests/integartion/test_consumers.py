from unittest.mock import AsyncMock, patch

from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase

from consumers.tests._helpers import TestKitchenConsumer


class ConsumerConnectionTest(TransactionTestCase):
    """
    Integration tests — exercises the full ASGI/Channels lifecycle using
    WebsocketCommunicator. get_unserved_orders is still mocked to avoid DB
    fixtures, but the WebSocket connect/receive/disconnect flow is real.
    """

    def _create_connection(self):
        return WebsocketCommunicator(TestKitchenConsumer.as_asgi(), "/ws/test/")

    @patch("consumers.base.get_unserved_orders", new_callable=AsyncMock)
    async def test_consumer_connect_sends_initial_orders(
        self, mock_get_unserved_orders
    ):
        mock_get_unserved_orders.return_value = [{"id": 1, "status": "pending"}]
        communicator = self._create_connection()

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        response = await communicator.receive_json_from()

        self.assertEqual(response["type"], "initial_orders")
        mock_get_unserved_orders.assert_awaited_once()
        await communicator.disconnect()

    @patch("consumers.base.get_unserved_orders", new_callable=AsyncMock)
    async def test_ping_returns_no_response(self, mock_get_unserved_orders):
        """Ping should be silently ignored — no message sent back to client."""
        mock_get_unserved_orders.return_value = []
        communicator = self._create_connection()

        await communicator.connect()
        await communicator.receive_json_from()  # consume initial_orders

        await communicator.send_json_to({"action": "ping"})

        self.assertTrue(await communicator.receive_nothing())
        await communicator.disconnect()

    @patch("consumers.base.get_unserved_orders", new_callable=AsyncMock)
    async def test_ping_keeps_connection_alive(self, mock_get_unserved_orders):
        """Connection should remain open and functional after multiple pings."""
        mock_get_unserved_orders.return_value = []
        communicator = self._create_connection()

        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from()  # consume initial_orders

        await communicator.send_json_to({"action": "ping"})
        await communicator.send_json_to({"action": "ping"})

        self.assertTrue(await communicator.receive_nothing())
        await communicator.disconnect()
