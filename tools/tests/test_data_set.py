from collections import namedtuple
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from model_bakery import baker

from order.models import Bill, Order, OrderItem, OrderItemAddition, Worker
from tools.data_set import BillData, BillSummary

SummaryScore = namedtuple(
    "SummaryScore", ["revenue", "revenue_cash", "revenue_card", "len"]
)


class BillSummaryTest(TestCase):
    def setUp(self):
        self.data_set_one = [
            {
                "id": 11,
                "payment_method": "card",
                "discount": 0,
                "guest_count": 2,
                "service__user__username": "waiter_1",
                "orders__order_items__id": 38,
                "orders__order_items__price_snapshot": Decimal("34.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 11,
                "payment_method": "card",
                "discount": 0,
                "guest_count": 2,
                "service__user__username": "waiter_1",
                "orders__order_items__id": 39,
                "orders__order_items__price_snapshot": Decimal("12.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 11,
                "payment_method": "card",
                "discount": 0,
                "guest_count": 2,
                "service__user__username": "waiter_1",
                "orders__order_items__id": 40,
                "orders__order_items__price_snapshot": Decimal("10.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 12,
                "payment_method": "card",
                "discount": 0,
                "guest_count": 2,
                "service__user__username": "waiter_2",
                "orders__order_items__id": 41,
                "orders__order_items__price_snapshot": Decimal("25.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": 7,
                "orders__order_items__order_item_additions__price_snapshot": Decimal(
                    "0.00"
                ),
            },
            {
                "id": 12,
                "payment_method": "card",
                "discount": 0,
                "guest_count": 2,
                "service__user__username": "waiter_2",
                "orders__order_items__id": 41,
                "orders__order_items__price_snapshot": Decimal("25.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": 8,
                "orders__order_items__order_item_additions__price_snapshot": Decimal(
                    "3.00"
                ),
            },
            {
                "id": 12,
                "payment_method": "card",
                "discount": 0,
                "guest_count": 2,
                "service__user__username": "waiter_2",
                "orders__order_items__id": 42,
                "orders__order_items__price_snapshot": Decimal("10.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
        ]
        self.data_set_one_summary = SummaryScore(
            Decimal("94.00"), Decimal("0.00"), Decimal("94.00"), 2
        )
        self.data_set_none_items = [
            {
                "id": 11,
                "payment_method": "card",
                "discount": 0,
                "guest_count": 2,
                "service__user__username": "waiter_1",
                "orders__order_items__id": None,
                "orders__order_items__price_snapshot": None,
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 12,
                "payment_method": "card",
                "discount": 0,
                "guest_count": 2,
                "service__user__username": "waiter_2",
                "orders__order_items__id": None,
                "orders__order_items__price_snapshot": None,
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
        ]
        self.data_set_none_items_summary = SummaryScore(
            Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), 2
        )
        self.data_set_group = [
            {
                "id": 11,
                "payment_method": "card",
                "discount": 0,
                "guest_count": 2,
                "service__user__username": "waiter_1",
                "orders__order_items__id": 38,
                "orders__order_items__price_snapshot": Decimal("34.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 11,
                "payment_method": "card",
                "discount": 0,
                "guest_count": 2,
                "service__user__username": "waiter_1",
                "orders__order_items__id": 39,
                "orders__order_items__price_snapshot": Decimal("12.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 11,
                "payment_method": "card",
                "discount": 0,
                "guest_count": 2,
                "service__user__username": "waiter_1",
                "orders__order_items__id": 40,
                "orders__order_items__price_snapshot": Decimal("10.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 12,
                "payment_method": "cash",
                "discount": 0,
                "guest_count": 2,
                "service__user__username": "waiter_2",
                "orders__order_items__id": 41,
                "orders__order_items__price_snapshot": Decimal("25.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": 7,
                "orders__order_items__order_item_additions__price_snapshot": Decimal(
                    "0.00"
                ),
            },
            {
                "id": 12,
                "payment_method": "cash",
                "discount": 0,
                "guest_count": 2,
                "service__user__username": "waiter_2",
                "orders__order_items__id": 41,
                "orders__order_items__price_snapshot": Decimal("25.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": 8,
                "orders__order_items__order_item_additions__price_snapshot": Decimal(
                    "3.00"
                ),
            },
            {
                "id": 12,
                "payment_method": "cash",
                "discount": 0,
                "guest_count": 2,
                "service__user__username": "waiter_2",
                "orders__order_items__id": 42,
                "orders__order_items__price_snapshot": Decimal("10.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
        ]
        self.data_set_group_summary = SummaryScore(
            Decimal("94.00"), Decimal("38.00"), Decimal("56.00"), 2
        )
        self.data_set_free = [
            {
                "id": 11,
                "payment_method": "card",
                "discount": 100,
                "guest_count": 2,
                "service__user__username": "waiter_1",
                "orders__order_items__id": 38,
                "orders__order_items__price_snapshot": Decimal("34.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 11,
                "payment_method": "card",
                "discount": 100,
                "guest_count": 2,
                "service__user__username": "waiter_1",
                "orders__order_items__id": 39,
                "orders__order_items__price_snapshot": Decimal("12.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 12,
                "payment_method": "card",
                "discount": 100,
                "guest_count": 2,
                "service__user__username": "waiter_2",
                "orders__order_items__id": 41,
                "orders__order_items__price_snapshot": Decimal("25.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": 8,
                "orders__order_items__order_item_additions__price_snapshot": Decimal(
                    "3.00"
                ),
            },
            {
                "id": 12,
                "payment_method": "card",
                "discount": 100,
                "guest_count": 2,
                "service__user__username": "waiter_2",
                "orders__order_items__id": 42,
                "orders__order_items__price_snapshot": Decimal("10.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
        ]

    def test_should_calculate_revenue_summary(self):
        bs = BillSummary.parse_from_qs(self.data_set_one)
        summary = bs.summary()
        with self.subTest(field="revenue"):
            self.assertEqual(summary["revenue"], self.data_set_one_summary.revenue)
        with self.subTest(field="revenue_cash"):
            self.assertEqual(
                summary["revenue_cash"], self.data_set_one_summary.revenue_cash
            )
        with self.subTest(field="revenue_card"):
            self.assertEqual(
                summary["revenue_card"], self.data_set_one_summary.revenue_card
            )

    def test_should_return_summary_with_zero_values(self):
        bs = BillSummary.parse_from_qs(self.data_set_none_items)
        summary = bs.summary()
        self.assertEqual(summary["revenue"], self.data_set_none_items_summary.revenue)
        self.assertEqual(
            summary["revenue_cash"], self.data_set_none_items_summary.revenue_cash
        )
        self.assertEqual(
            summary["revenue_card"], self.data_set_none_items_summary.revenue_card
        )

    def test_should_return_correct_length(self):
        bs = BillSummary.parse_from_qs(self.data_set_one)
        self.assertEqual(len(bs), self.data_set_one_summary.len)

    def test_should_calculate_revenue_grouped_by_payment_method(self):
        bs = BillSummary.parse_from_qs(self.data_set_group)
        summary = bs.count_revenue_by_group()
        self.assertEqual(
            summary["revenue_cash"], self.data_set_group_summary.revenue_cash
        )
        self.assertEqual(
            summary["revenue_card"], self.data_set_group_summary.revenue_card
        )

    def test_should_apply_discount(self):
        data = [
            {
                "id": 11,
                "payment_method": "card",
                "discount": 10,
                "guest_count": 2,
                "service__user__username": "waiter_1",
                "orders__order_items__id": 1,
                "orders__order_items__price_snapshot": Decimal("100.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
        ]
        bs = BillSummary.parse_from_qs(data)
        summary = bs.summary()
        self.assertEqual(summary["revenue"], Decimal("90.00"))

    def test_should_return_zero_when_discount_equal_100(self):
        bs = BillSummary.parse_from_qs(self.data_set_free)

        with self.subTest(field="revenue"):
            self.assertEqual(bs.count_revenue(), Decimal("0.00"))

        with self.subTest(field="avg_per_guests"):
            self.assertEqual(bs.avg_per_plate(), Decimal("0.00"))

        with self.subTest(field="guest_count"):
            self.assertEqual(bs.count_guests(), 4)

        with self.subTest(field="waiter_summary"):
            waiter_summary = bs.calculate_waiter_stats()
            self.assertEqual(waiter_summary["waiter_1"]["bills"], 1)
            self.assertEqual(waiter_summary["waiter_1"]["revenue"], Decimal("0.00"))
            self.assertEqual(waiter_summary["waiter_2"]["bills"], 1)
            self.assertEqual(waiter_summary["waiter_2"]["revenue"], Decimal("0.00"))


class BillSummaryEmptyTest(TestCase):
    def setUp(self):
        self.bills = {
            1: BillData(1, "test", 0, {}, 0, "waiter_1"),
            2: BillData(2, "test", 0, {}, 0, "waiter_2"),
        }

    def test_should_return_zero_number_of_guests(self):
        bs = BillSummary(self.bills)
        self.assertEqual(bs.count_guests(), 0)

    def test_should_return_zero_avg_per_plate(self):
        bs = BillSummary(self.bills)
        self.assertEqual(bs.avg_per_plate(), Decimal(0))


class BillSummaryMockTest(TestCase):
    @patch("tools.data_set.BillSummary.count_revenue", return_value=Decimal("300.00"))
    def test_should_calculate_avg_per_plate(self, mock_count_revenue):
        bs = BillSummary(
            {
                1: BillData(1, "test", 0, {}, 3, "waiter_1"),
                2: BillData(1, "test", 0, {}, 2, "waiter_2"),
            }
        )
        avg_plate = bs.avg_per_plate()
        mock_count_revenue.assert_called_once()
        self.assertAlmostEqual(avg_plate, Decimal(60), places=2)


class WaiterStatsCalculationTest(TestCase):
    """
    Tests for waiter statistics calculation in BillSummary.

    Each test is independent and creates its own data setup.
    This ensures test isolation and makes debugging easier.
    """

    def _create_waiter(self, username: str) -> Worker:
        """Create a waiter with given username."""
        return baker.make(Worker, user__username=username)

    def _create_bill_with_item(
        self, waiter: Worker, price: Decimal, quantity: int = 1, discount: int = 0
    ) -> Bill:
        """
        Create a bill with a single order item.

        Args:
            waiter: Waiter serving this bill
            price: Item price
            quantity: Item quantity
            discount: Discount percentage (0-100)

        Returns:
            Created Bill instance
        """
        bill = baker.make(Bill, service=waiter, discount=discount)
        order = baker.make(Order, bill=bill)
        baker.make(OrderItem, price_snapshot=price, quantity=quantity, order=order)
        return bill

    def _get_waiter_stats(self, bill_ids: list[int] | None = None) -> dict:
        """
        Get waiter statistics for given bills.

        Args:
            bill_ids: List of bill IDs. If None, queries all bills.

        Returns:
            Dictionary with waiter stats
        """
        queryset = Bill.objects.all()

        if bill_ids is not None:
            queryset = queryset.filter(id__in=bill_ids)

        qs = queryset.prefetch_related(
            "orders__order_items",
            "orders__order_items__order_item_additions",
            "service__user",
        ).values(
            "id",
            "payment_method",
            "discount",
            "service__user__username",
            "guest_count",
            "orders__order_items__id",
            "orders__order_items__price_snapshot",
            "orders__order_items__quantity",
            "orders__order_items__order_item_additions__pk",
            "orders__order_items__order_item_additions__price_snapshot",
        )

        summary = BillSummary.parse_from_qs(qs)
        return summary.calculate_waiter_stats()

    def test_should_count_bills_per_waiter(self):
        """Each waiter should have correct bill count."""
        # Arrange
        john = self._create_waiter("john")
        alice = self._create_waiter("alice")

        john_bill_1 = self._create_bill_with_item(john, Decimal("10.00"))
        john_bill_2 = self._create_bill_with_item(john, Decimal("20.00"))
        alice_bill = self._create_bill_with_item(alice, Decimal("30.00"))

        # Act
        stats = self._get_waiter_stats([john_bill_1.id, john_bill_2.id, alice_bill.id])

        # Assert
        self.assertEqual(stats["john"]["bills"], 2)
        self.assertEqual(stats["alice"]["bills"], 1)

    def test_should_sum_revenue_per_waiter(self):
        """Revenue should be summed across all waiter's bills."""
        # Arrange
        bob = self._create_waiter("bob")

        bill_1 = self._create_bill_with_item(bob, Decimal("50.00"))
        bill_2 = self._create_bill_with_item(bob, Decimal("30.00"))

        # Act
        stats = self._get_waiter_stats([bill_1.id, bill_2.id])

        # Assert
        expected_revenue = Decimal("80.00")  # 50 + 30
        self.assertEqual(stats["bob"]["revenue"], expected_revenue)

    def test_should_apply_discount_to_revenue(self):
        """Discount should reduce waiter's revenue."""
        # Arrange
        charlie = self._create_waiter("charlie")

        bill = self._create_bill_with_item(
            charlie, price=Decimal("100.00"), discount=20  # 20% off
        )

        # Act
        stats = self._get_waiter_stats([bill.id])

        # Assert
        expected_revenue = Decimal("80.00")  # 100 - 20%
        self.assertEqual(stats["charlie"]["revenue"], expected_revenue)

    def test_should_multiply_price_by_quantity(self):
        """Item quantity should multiply the price."""
        # Arrange
        dave = self._create_waiter("dave")

        bill = self._create_bill_with_item(dave, price=Decimal("10.00"), quantity=3)

        # Act
        stats = self._get_waiter_stats([bill.id])

        # Assert
        expected_revenue = Decimal("30.00")  # 10 * 3
        self.assertEqual(stats["dave"]["revenue"], expected_revenue)

    def test_should_include_additions_in_revenue(self):
        """
        Order item additions should be included in revenue calculation.
        Additions are also multiplied by item quantity.
        """
        # Arrange
        eve = self._create_waiter("eve")

        bill = baker.make(Bill, service=eve, discount=0)
        order = baker.make(Order, bill=bill)

        # Item: 10.00 * 3 = 30.00
        order_item = baker.make(
            OrderItem, price_snapshot=Decimal("10.00"), quantity=3, order=order
        )

        # Addition 1: 2.00 * 3 = 6.00
        baker.make(
            OrderItemAddition, price_snapshot=Decimal("2.00"), order_item=order_item
        )

        # Addition 2: 1.00 * 3 = 3.00
        baker.make(
            OrderItemAddition, price_snapshot=Decimal("1.00"), order_item=order_item
        )

        # Act
        stats = self._get_waiter_stats([bill.id])

        # Assert
        expected_revenue = Decimal("39.00")  # (10 + 2 + 1) * 3
        self.assertEqual(stats["eve"]["revenue"], expected_revenue)

    def test_should_handle_multiple_items_per_bill(self):
        """Multiple order items on single bill should be summed."""
        # Arrange
        frank = self._create_waiter("frank")

        bill = baker.make(Bill, service=frank, discount=0)
        order = baker.make(Order, bill=bill)

        # Item 1: 10.00 * 2 = 20.00
        baker.make(OrderItem, price_snapshot=Decimal("10.00"), quantity=2, order=order)

        # Item 2: 15.00 * 1 = 15.00
        baker.make(OrderItem, price_snapshot=Decimal("15.00"), quantity=1, order=order)

        # Act
        stats = self._get_waiter_stats([bill.id])

        # Assert
        expected_revenue = Decimal("35.00")  # 20 + 15
        self.assertEqual(stats["frank"]["revenue"], expected_revenue)

    def test_should_separate_stats_per_waiter(self):
        """Each waiter should have independent statistics."""
        # Arrange
        grace = self._create_waiter("grace")
        henry = self._create_waiter("henry")

        grace_bill = self._create_bill_with_item(grace, Decimal("100.00"))
        henry_bill = self._create_bill_with_item(henry, Decimal("50.00"))

        # Act
        stats = self._get_waiter_stats([grace_bill.id, henry_bill.id])

        # Assert
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats["grace"]["revenue"], Decimal("100.00"))
        self.assertEqual(stats["henry"]["revenue"], Decimal("50.00"))

    def test_should_return_empty_dict_for_no_bills(self):
        """Empty bills should return empty statistics dictionary."""
        # Arrange (nothing!)

        # Act
        summary = BillSummary({})
        stats = summary.calculate_waiter_stats()

        # Assert
        self.assertEqual(stats, {})

    def test_should_handle_zero_revenue_bill(self):
        """Bill with 100% discount should have zero revenue."""
        # Arrange
        ivy = self._create_waiter("ivy")

        bill = self._create_bill_with_item(
            ivy, price=Decimal("50.00"), discount=100  # Free!
        )

        # Act
        stats = self._get_waiter_stats([bill.id])

        # Assert
        self.assertEqual(stats["ivy"]["revenue"], Decimal("0.00"))
        self.assertEqual(stats["ivy"]["bills"], 1)


class WaiterStatsAggregationTest(TestCase):
    """
    Tests for aggregate waiter statistics.

    All tests in this class use the same restaurant shift scenario,
    so setUpTestData is appropriate here.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Setup a complete restaurant shift with multiple waiters.

        This is appropriate because:
        1. ALL tests use this exact scenario
        2. Tests are read-only (no modifications)
        3. Setup is expensive (many objects)
        """
        # Morning shift waiters
        cls.john = baker.make(Worker, user__username="john")
        cls.alice = baker.make(Worker, user__username="alice")
        cls.bob = baker.make(Worker, user__username="bob")

        # Create bills for each waiter
        # John: 3 bills
        for _ in range(3):
            bill = baker.make(Bill, service=cls.john, discount=0)
            order = baker.make(Order, bill=bill)
            baker.make(
                OrderItem, order=order, price_snapshot=Decimal("20.00"), quantity=1
            )

        # Alice: 2 bills
        for _ in range(2):
            bill = baker.make(Bill, service=cls.alice, discount=0)
            order = baker.make(Order, bill=bill)
            baker.make(
                OrderItem, order=order, price_snapshot=Decimal("30.00"), quantity=1
            )

        # Bob: 1 bill
        bill = baker.make(Bill, service=cls.bob, discount=0)
        order = baker.make(Order, bill=bill)
        baker.make(OrderItem, order=order, price_snapshot=Decimal("50.00"), quantity=1)

    def _get_all_stats(self):
        """Helper to get stats for all bills in database."""
        qs = Bill.objects.prefetch_related(
            "orders__order_items",
            "orders__order_items__order_item_additions",
            "service__user",
        ).values(
            "id",
            "payment_method",
            "discount",
            "service__user__username",
            "guest_count",
            "orders__order_items__id",
            "orders__order_items__price_snapshot",
            "orders__order_items__quantity",
            "orders__order_items__order_item_additions__pk",
            "orders__order_items__order_item_additions__price_snapshot",
        )
        return BillSummary.parse_from_qs(qs).calculate_waiter_stats()

    def test_should_have_stats_for_all_waiters(self):
        """All waiters in shift should appear in statistics."""
        # Act
        stats = self._get_all_stats()

        # Assert
        self.assertEqual(len(stats), 3)
        self.assertIn("john", stats)
        self.assertIn("alice", stats)
        self.assertIn("bob", stats)

    def test_john_should_have_most_bills(self):
        """John served most customers during the shift."""
        # Act
        stats = self._get_all_stats()

        # Assert
        self.assertEqual(stats["john"]["bills"], 3)
        self.assertGreater(stats["john"]["bills"], stats["alice"]["bills"])
        self.assertGreater(stats["john"]["bills"], stats["bob"]["bills"])

    def test_total_bills_should_match_sum(self):
        """Total bills should equal sum of individual waiter bills."""
        # Act
        stats = self._get_all_stats()

        # Assert
        total_bills = sum(waiter["bills"] for waiter in stats.values())
        self.assertEqual(total_bills, 6)  # 3 + 2 + 1

    def test_total_revenue_should_match_sum(self):
        """Total revenue should equal sum of individual waiter revenues."""
        # Act
        stats = self._get_all_stats()

        # Assert
        total_revenue = sum(waiter["revenue"] for waiter in stats.values())
        expected_total = Decimal("170.00")  # 60 + 60 + 50
        self.assertEqual(total_revenue, expected_total)


class WaiterStatsPerformanceTest(TestCase):
    """
    Performance tests for waiter statistics.

    When testing with many objects, create them efficiently.
    """

    def test_should_handle_many_bills_efficiently(self):
        """Statistics calculation should work with large datasets."""
        # Arrange - create 100 bills efficiently
        waiter = baker.make(Worker, user__username="speedy")

        bills = []
        for i in range(100):
            bill = baker.make(Bill, service=waiter, discount=0)
            order = baker.make(Order, bill=bill)
            baker.make(
                OrderItem, order=order, price_snapshot=Decimal("10.00"), quantity=1
            )
            bills.append(bill)

        # Act
        qs = (
            Bill.objects.filter(id__in=[b.id for b in bills])
            .prefetch_related(
                "orders__order_items",
                "orders__order_items__order_item_additions",
                "service__user",
            )
            .values(
                "id",
                "payment_method",
                "discount",
                "service__user__username",
                "guest_count",
                "orders__order_items__id",
                "orders__order_items__price_snapshot",
                "orders__order_items__quantity",
                "orders__order_items__order_item_additions__pk",
                "orders__order_items__order_item_additions__price_snapshot",
            )
        )

        summary = BillSummary.parse_from_qs(qs)
        stats = summary.calculate_waiter_stats()

        # Assert
        self.assertEqual(stats["speedy"]["bills"], 100)
        self.assertEqual(stats["speedy"]["revenue"], Decimal("1000.00"))
