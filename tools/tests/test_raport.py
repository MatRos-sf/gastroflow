from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from order.models import Location, StatusBill
from tools.raport_calculator import CountBillStatus, OrderItemsQuantity


class TestCountBillStatus(TestCase):
    FIRST_DAY_CREATED_AT = timezone.make_aware(datetime(2022, 1, 1))
    SECOND_DAY_CREATED_AT = timezone.make_aware(datetime(2022, 1, 2))
    OPEN_BILLS = 5
    CLOSED_BILLS_FIRST_DAY = 3
    CLOSED_BILLS_SECOND_DAY = 3

    def setUp(self):
        for _ in range(self.OPEN_BILLS):
            baker.make(
                "order.Bill",
                created_at=self.FIRST_DAY_CREATED_AT,
                status=StatusBill.OPEN,
            )
        for _ in range(self.CLOSED_BILLS_FIRST_DAY):
            baker.make(
                "order.Bill",
                created_at=self.FIRST_DAY_CREATED_AT,
                status=StatusBill.CLOSED,
            )
        for _ in range(self.CLOSED_BILLS_SECOND_DAY):
            baker.make(
                "order.Bill",
                created_at=self.SECOND_DAY_CREATED_AT,
                status=StatusBill.CLOSED,
            )

    def test_count_bill_status(self):
        """Test counting bills by status for a given date."""
        count_bill = CountBillStatus()
        self.assertEqual(
            count_bill.calculate(self.FIRST_DAY_CREATED_AT, self.FIRST_DAY_CREATED_AT),
            {"opened": self.OPEN_BILLS, "closed": self.CLOSED_BILLS_FIRST_DAY},
        )


class TestOrderItemsQuantity(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.from_date = timezone.make_aware(datetime(2025, 10, 28, 0, 0))
        cls.to_date = timezone.make_aware(datetime(2025, 10, 28, 23, 59, 59))

        cls.quantity_kitchen = (1, 2, 3)
        cls.quantity_bar = (4, 5)
        # kitchen
        for q in cls.quantity_kitchen:
            baker.make(
                "order.OrderItem",
                quantity=q,
                finished_at=cls.from_date,
                order__category=Location.KITCHEN,
            )

        # bar
        for q in cls.quantity_bar:
            baker.make(
                "order.OrderItem",
                quantity=q,
                finished_at=cls.from_date,
                order__category=Location.BAR,
            )

    def test_order_item_quantity(self):
        oiq = OrderItemsQuantity()
        data = oiq.calculate(self.from_date, self.to_date)

        self.assertEqual(data["kitchen"], sum(self.quantity_kitchen))
        self.assertEqual(data["bar"], sum(self.quantity_bar))
        self.assertEqual(data["total"], sum(self.quantity_kitchen + self.quantity_bar))

    def test_order_item_quantity_with_different_date(self):
        """
        Verify that the order item quantity is calculated correctly for a given date range.
        """
        new_date = timezone.make_aware(datetime(2025, 10, 29, 0, 0))
        expected_more = 2
        instance = baker.make(
            "order.OrderItem",
            quantity=expected_more,
            finished_at=new_date,
            order__category=Location.KITCHEN,
        )

        oiq = OrderItemsQuantity()
        data = oiq.calculate(self.from_date, new_date)

        self.assertEqual(data["kitchen"], sum(self.quantity_kitchen) + 2)
        self.assertEqual(data["bar"], sum(self.quantity_bar))
        self.assertEqual(
            data["total"], sum(self.quantity_kitchen + self.quantity_bar) + 2
        )

        instance.delete()
