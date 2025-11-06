from collections import namedtuple
from decimal import Decimal

from django.test import TestCase

from tools.data_set import BillSummary

SummaryScore = namedtuple(
    "SummaryScore", ["revenue", "revenue_cash", "revenue_card", "len"]
)


class BillSummaryTest(TestCase):
    def setUp(self):
        self.data_set_one = [
            {
                "id": 11,
                "payment_method": "karta",
                "discount": 0,
                "orders__order_items__id": 38,
                "orders__order_items__price_snapshot": Decimal("34.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 11,
                "payment_method": "karta",
                "discount": 0,
                "orders__order_items__id": 39,
                "orders__order_items__price_snapshot": Decimal("12.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 11,
                "payment_method": "karta",
                "discount": 0,
                "orders__order_items__id": 40,
                "orders__order_items__price_snapshot": Decimal("10.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 12,
                "payment_method": "karta",
                "discount": 0,
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
                "payment_method": "karta",
                "discount": 0,
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
                "payment_method": "karta",
                "discount": 0,
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
                "payment_method": "karta",
                "discount": 0,
                "orders__order_items__id": None,
                "orders__order_items__price_snapshot": None,
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 12,
                "payment_method": "karta",
                "discount": 0,
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
                "payment_method": "karta",
                "discount": 0,
                "orders__order_items__id": 38,
                "orders__order_items__price_snapshot": Decimal("34.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 11,
                "payment_method": "karta",
                "discount": 0,
                "orders__order_items__id": 39,
                "orders__order_items__price_snapshot": Decimal("12.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 11,
                "payment_method": "karta",
                "discount": 0,
                "orders__order_items__id": 40,
                "orders__order_items__price_snapshot": Decimal("10.00"),
                "orders__order_items__quantity": 1,
                "orders__order_items__order_item_additions__pk": None,
                "orders__order_items__order_item_additions__price_snapshot": None,
            },
            {
                "id": 12,
                "payment_method": "gotówka",
                "discount": 0,
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
                "payment_method": "gotówka",
                "discount": 0,
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
                "payment_method": "gotówka",
                "discount": 0,
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
                "payment_method": "karta",
                "discount": 10,
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
