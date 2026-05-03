from decimal import Decimal

from django.core.validators import ValidationError
from django.test import TestCase
from model_bakery import baker

from order.models import OrderItem


class TestOrderItem(TestCase):
    def _make_order_item_models(self, **kwargs):
        return baker.make(OrderItem, **kwargs)

    def test_order_item_line_total(self):
        """Should calculate raw cost for Item"""
        price_snapshot = 10
        quantity = 2
        order_item_instance = self._make_order_item_models(
            price_snapshot=price_snapshot, quantity=quantity
        )
        expected = Decimal(price_snapshot * quantity)
        self.assertEqual(order_item_instance.line_subtotal, expected)

    def test_order_item_line_total_after(self):
        """Should return price without discount"""
        price_snapshot = 10
        quantity = 2
        line_discount_amount = Decimal("10.00")
        order_item_instance = self._make_order_item_models(
            price_snapshot=price_snapshot,
            quantity=quantity,
            line_discount_amount=line_discount_amount,
        )
        expected = Decimal(price_snapshot * quantity) - line_discount_amount
        self.assertEqual(order_item_instance.line_final_total, expected)

    def test_should_not_allow_negative_line_total_after(self):
        """Should not allow negative line_total_after"""
        price_snapshot = 10
        quantity = 2
        line_discount_amount = Decimal("21.00")

        with self.assertRaises(ValidationError):
            self._make_order_item_models(
                price_snapshot=price_snapshot,
                quantity=quantity,
                line_discount_amount=line_discount_amount,
            )

        self.assertEqual(OrderItem.objects.count(), 0)
