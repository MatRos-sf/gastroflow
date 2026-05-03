from unittest.mock import patch

from django.test import TestCase
from parameterized import parameterized

from order.factories import OrderItemMixinFactory, OrderMixinFactory
from order.models import OrderItem, OrderItemStatus, StatusOrder
from order.queries import update_batch_order_items_status


class TestUpdateBatchOrderItemsStatus(
    OrderMixinFactory, OrderItemMixinFactory, TestCase
):
    def setUp(self):
        self.order = self.make_order()

    @patch("order.queries.get_order", return_value=None)
    def test_should_return_none_when_order_not_found(self, mock_get_order):
        self.assertIsNone(
            update_batch_order_items_status(self.order.id + 1, StatusOrder.PREPARING)
        )

    @parameterized.expand(
        [
            OrderItemStatus.PREPARING,
            OrderItemStatus.READY,
        ]
    )
    def test_should_change_order_item_status(self):
        self.make_order_item(
            order=self.order, status=OrderItemStatus.WAITING, _quantity=2
        )

        update_batch_order_items_status(self.order.id, StatusOrder.PREPARING)

        self.assertEqual(
            OrderItem.objects.filter(
                order=self.order, status=OrderItemStatus.PREPARING
            ).count(),
            2,
        )
