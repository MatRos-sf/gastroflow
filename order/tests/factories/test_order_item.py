from django.test import TestCase

from order.factories import OrderItemMixinFactory, OrderMixinFactory
from order.models import Order, OrderItem, OrderItemAddition


class TestOrderItemFactory(OrderItemMixinFactory, OrderMixinFactory, TestCase):
    def test_should_create_order_item(self):
        order_item = self.make_order_item()
        self.assertIsInstance(order_item, OrderItem)

    def test_should_create_5_order_items(self):
        self.make_order_item(_quantity=5)
        self.assertEqual(OrderItem.objects.count(), 5)

    def test_should_create_order_with_one_order_item(self):
        order = self.make_order()
        order_item = self.make_order_item(order=order)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(Order.objects.get(pk=order.id).order_items.first(), order_item)

    def test_should_create_order_item_with_additions(self):
        order_item = self.make_order_item_with_additions(addition_count=2)
        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(
            OrderItemAddition.objects.filter(order_item=order_item).count(), 2
        )
