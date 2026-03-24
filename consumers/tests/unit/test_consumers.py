import json
from unittest.mock import AsyncMock, MagicMock, patch

from django.test import TestCase

from consumers.base import ConsumerActionType
from consumers.tests._helpers import TestKitchenConsumer
from order.models import OrderItemStatus, StatusOrder


class ReceiveUnitTest(TestCase):
    def setUp(self):
        self.consumer = TestKitchenConsumer()

    async def test_dispatches_to_correct_handler(self):
        self.consumer.handle_ping = AsyncMock()
        await self.consumer.receive(json.dumps({"action": "ping"}))

        self.consumer.handle_ping.assert_awaited_once_with({"action": "ping"})

    async def test_passes_full_data_to_handler(self):
        self.consumer.handle_item_done = AsyncMock()
        data = {"action": "item_done", "item_id": 1, "order_id": 10}
        await self.consumer.receive(json.dumps(data))

        self.consumer.handle_item_done.assert_awaited_once_with(data)

    async def test_falls_back_to_handle_unknown_for_missing_action(self):
        self.consumer.handle_unknown = AsyncMock()
        await self.consumer.receive(json.dumps({}))

        self.consumer.handle_unknown.assert_awaited_once_with({})

    async def test_falls_back_to_handle_unknown_for_unrecognized_action(self):
        self.consumer.handle_unknown = AsyncMock()
        data = {"action": "nonexistent_action"}
        await self.consumer.receive(json.dumps(data))

        self.consumer.handle_unknown.assert_awaited_once_with(data)


class HandlePingUnitTest(TestCase):
    def setUp(self):
        self.consumer = TestKitchenConsumer()

    @patch("consumers.base.logger")
    async def test_handle_ping_logs_debug_message(self, mock_logger):
        await self.consumer.handle_ping({})

        mock_logger.debug.assert_called_once_with(
            f"[{self.consumer.CATEGORY}] Received ping, connection is active."
        )

    async def test_handle_ping_returns_none(self):
        result = await self.consumer.handle_ping({})

        self.assertIsNone(result)


class HandleItemDoneUnitTest(TestCase):
    def setUp(self):
        self.consumer = TestKitchenConsumer()
        self.consumer.send = AsyncMock()

    def _make_queryset_mock(self):
        mock_qs = MagicMock()
        mock_qs.aupdate = AsyncMock()
        return mock_qs

    @patch("consumers.base.OrderItem.objects.filter")
    async def test_updates_item_status_to_ready(self, mock_filter):
        mock_filter.return_value = self._make_queryset_mock()

        await self.consumer.handle_item_done({"item_id": 1, "order_id": 10})

        mock_filter.assert_called_once_with(id=1)
        mock_filter.return_value.aupdate.assert_awaited_once_with(
            status=OrderItemStatus.READY
        )

    @patch("consumers.base.dispatch_item_done_notification", new_callable=AsyncMock)
    @patch("consumers.base.OrderItem.objects.filter")
    async def test_sends_notification_after_status_update(
        self, mock_filter, mock_dispatch
    ):
        mock_filter.return_value = self._make_queryset_mock()

        await self.consumer.handle_item_done({"item_id": 1, "order_id": 10})

        mock_dispatch.assert_awaited_once_with(10, 1)

    @patch("consumers.base.dispatch_item_done_notification", new_callable=AsyncMock)
    @patch("consumers.base.OrderItem.objects.filter")
    async def test_does_nothing_when_item_id_missing(self, mock_filter, mock_dispatch):
        await self.consumer.handle_item_done({"order_id": 10})

        mock_filter.assert_not_called()
        mock_dispatch.assert_not_awaited()

    @patch("consumers.base.OrderItem.objects.filter")
    async def test_sends_error_response_when_item_id_missing(self, mock_filter):
        await self.consumer.handle_item_done({"order_id": 10})

        sent = json.loads(self.consumer.send.call_args[0][0])
        self.assertEqual(sent["type"], "error")
        self.assertEqual(sent["action"], "item_done")


class HandleOrderPreparingUnitTest(TestCase):
    def setUp(self):
        self.consumer = TestKitchenConsumer()
        self.consumer.send = AsyncMock()
        self.consumer._update_order_status = AsyncMock()

    async def test_calls_update_with_preparing_status(self):
        await self.consumer.handle_order_preparing({"order_id": 5})

        self.consumer._update_order_status.assert_awaited_once_with(
            5, StatusOrder.PREPARING
        )

    async def test_sends_error_when_order_id_missing(self):
        await self.consumer.handle_order_preparing({})

        self.consumer._update_order_status.assert_not_awaited()
        sent = json.loads(self.consumer.send.call_args[0][0])
        self.assertEqual(sent["type"], "error")
        self.assertEqual(sent["action"], "preparing")


class HandleOrderReadyUnitTest(TestCase):
    def setUp(self):
        self.consumer = TestKitchenConsumer()
        self.consumer.send = AsyncMock()
        self.consumer._update_order_status = AsyncMock()

    async def test_calls_update_with_ready_status(self):
        await self.consumer.handle_order_ready({"order_id": 5})

        self.consumer._update_order_status.assert_awaited_once_with(
            5, StatusOrder.READY
        )

    async def test_sends_error_when_order_id_missing(self):
        await self.consumer.handle_order_ready({})

        self.consumer._update_order_status.assert_not_awaited()
        sent = json.loads(self.consumer.send.call_args[0][0])
        self.assertEqual(sent["type"], "error")
        self.assertEqual(sent["action"], "ready")


class UpdateOrderStatusUnitTest(TestCase):
    def setUp(self):
        self.consumer = TestKitchenConsumer()
        self.consumer.channel_layer = AsyncMock()

    @patch("consumers.base.update_batch_order_items_status")
    async def test_calls_update_batch_with_correct_args(self, mock_update):
        await self.consumer._update_order_status(5, StatusOrder.PREPARING)

        mock_update.assert_called_once_with(5, StatusOrder.PREPARING)

    @patch("consumers.base.update_batch_order_items_status")
    async def test_broadcasts_to_group(self, mock_update):
        await self.consumer._update_order_status(5, StatusOrder.PREPARING)

        self.consumer.channel_layer.group_send.assert_awaited_once_with(
            self.consumer.GROUP_NAME,
            {
                "type": ConsumerActionType.ORDER_STATUS_UPDATE,
                "order_id": 5,
                "new_status": StatusOrder.PREPARING,
            },
        )
