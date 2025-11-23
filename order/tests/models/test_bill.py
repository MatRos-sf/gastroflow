from decimal import Decimal

from django.core.validators import ValidationError
from django.test import TestCase
from model_bakery import baker
from parameterized import parameterized

from order.models import Bill, Order, OrderItem, OrderItemAddition


class TestBill(TestCase):
    def _create_order_item_models(self, **kwargs):
        return baker.make(OrderItem, **kwargs)

    def _create_order_item_addition_models(self, **kwargs):
        return baker.make(OrderItemAddition, **kwargs)

    def _create_order_models(self, **kwargs):
        return baker.make(Order, **kwargs)

    def _create_bill_models(self, **kwargs):
        return baker.make(Bill, **kwargs)

    def test_should_add_discount_for_all_models_when_user_call_add_discount(self):
        """
        Test add 5% discount for a Bill.
        Total: (25*2) + (3*2) + (1*2) + (9*1) + (18*1) + (2*1) = 50 + 6 + 2 + 9 + 18 + 2 = 87
        Discount 5%: 87 * 0.05 = 4.35
        Expected total: 87 - 4.35 = 82.65
        """
        self.bill = self._create_bill_models(discount=0)
        self.order_one = self._create_order_models(bill=self.bill)
        self.order_two = self._create_order_models(bill=self.bill)

        self.order_dish_one = self._create_order_item_models(
            order=self.order_one, price_snapshot=25, quantity=2
        )
        self.first_additions_to_dish_one = self._create_order_item_addition_models(
            order_item=self.order_dish_one, price_snapshot=3, quantity=2
        )
        self.second_additions_to_dish_one = self._create_order_item_addition_models(
            order_item=self.order_dish_one, price_snapshot=1, quantity=2
        )

        self.order_dish_two = self._create_order_item_models(
            order=self.order_two, price_snapshot=9, quantity=1
        )
        self.order_dish_three = self._create_order_item_models(
            order=self.order_two, price_snapshot=18, quantity=1
        )
        self.first_additions_to_dish_three = self._create_order_item_addition_models(
            order_item=self.order_dish_three, price_snapshot=2, quantity=1
        )

        self.bill.add_discount(5)

        self.bill.refresh_from_db()

        self.assertEqual(self.bill.discount, 5)
        self.assertEqual(self.bill.total, Decimal("82.65"))

        self.order_dish_one.refresh_from_db()
        self.first_additions_to_dish_one.refresh_from_db()
        self.second_additions_to_dish_one.refresh_from_db()
        self.order_dish_two.refresh_from_db()
        self.order_dish_three.refresh_from_db()
        self.first_additions_to_dish_three.refresh_from_db()

        self.assertAlmostEqual(
            self.order_dish_one.line_discount_amount, Decimal("2.5"), places=2
        )

        self.assertAlmostEqual(
            self.first_additions_to_dish_one.line_discount_amount,
            Decimal("0.3"),
            places=2,
        )

    @parameterized.expand([-1, 101, 200])
    def test_should_not_add_discount_if_discount_is_invalid(self, discount):
        self.bill = self._create_bill_models(discount=0)
        with self.assertRaises(ValidationError):
            self.bill.add_discount(discount)
