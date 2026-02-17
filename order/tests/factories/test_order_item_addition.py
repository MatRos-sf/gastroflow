from decimal import Decimal

from django.test import TestCase

from order.factories import OrderItemAdditionMixinFactory, OrderItemMixinFactory
from order.models import OrderItemAddition


class TestOrderItemAdditionFactory(
    OrderItemAdditionMixinFactory, OrderItemMixinFactory, TestCase
):
    def test_should_create_addition(self):
        addition = self.make_addition()
        self.assertIsInstance(addition, OrderItemAddition)

    def test_should_create_addition_linked_to_order_item(self):
        order_item = self.make_order_item()
        addition = self.make_addition(
            order_item=order_item, price_snapshot=Decimal("3.50")
        )
        self.assertEqual(addition.order_item, order_item)
        self.assertEqual(addition.price_snapshot, Decimal("3.50"))
