from collections import namedtuple
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

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


class BillSummaryEmptyTest(TestCase):
    def setUp(self):
        self.bills = {
            1: BillData(1, "test", 0, {}, 0),
            2: BillData(2, "test", 0, {}, 0),
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
                1: BillData(1, "test", 0, {}, 3),
                2: BillData(1, "test", 0, {}, 2),
            }
        )
        avg_plate = bs.avg_per_plate()
        mock_count_revenue.assert_called_once()
        self.assertAlmostEqual(avg_plate, Decimal(60), places=2)
