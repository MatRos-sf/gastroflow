from django.test import TestCase

from menu.models import Location
from order.factories import OrderMixinFactory
from order.models import Order, OrderItem


class TestOrderFactory(OrderMixinFactory, TestCase):
    def test_should_create_order(self):
        self.make_order()
        self.assertEqual(Order.objects.count(), 1)

    def test_should_create_5_orders(self):
        self.make_order(_quantity=5)
        self.assertEqual(Order.objects.count(), 5)

    def test_should_create_kitchen_order(self):
        order = self.make_kitchen_order()
        self.assertEqual(order.category, Location.KITCHEN)

    def test_should_create_bar_order(self):
        order = self.make_bar_order()
        self.assertEqual(order.category, Location.BAR)

    def test_should_create_order_with_items(self):
        order = self.make_order_with_items(item_count=3)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 3)
