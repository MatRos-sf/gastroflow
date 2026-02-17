from unittest.mock import patch

from django.test import TestCase
from model_bakery import baker

from consumers.serializers import serialize_items_from_order, serialize_order
from menu.models import Location
from order.models import NotificationStatus, StatusOrder


class SerializeItemsFromOrderTests(TestCase):
    def setUp(self):
        self.worker = baker.make("worker.Worker")
        self.bill = baker.make("order.Bill", service=self.worker)
        self.order = baker.make("order.Order", bill=self.bill)

    def test_serializes_single_item(self):
        item = baker.make(
            "order.OrderItem",
            order=self.order,
            name_snapshot="Pierogi",
            price_snapshot="15.00",
            quantity=2,
            note="extra butter",
        )

        result = serialize_items_from_order(self.order)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], item.id)
        self.assertEqual(result[0]["name_snapshot"], "Pierogi")
        self.assertEqual(result[0]["quantity"], 2)
        self.assertEqual(result[0]["note"], "extra butter")

    def test_serializes_multiple_items_ordered_by_name(self):
        baker.make(
            "order.OrderItem",
            order=self.order,
            name_snapshot="Zurek",
            price_snapshot="12.00",
        )
        baker.make(
            "order.OrderItem",
            order=self.order,
            name_snapshot="Bigos",
            price_snapshot="18.00",
        )

        result = serialize_items_from_order(self.order)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name_snapshot"], "Bigos")
        self.assertEqual(result[1]["name_snapshot"], "Zurek")

    def test_returns_empty_list_for_order_without_items(self):
        result = serialize_items_from_order(self.order)

        self.assertEqual(result, [])

    def test_is_done_true_when_notification_status_wait(self):
        item = baker.make(
            "order.OrderItem",
            order=self.order,
            name_snapshot="Soup",
            price_snapshot="10.00",
        )
        notification = item.notification
        notification.status = NotificationStatus.WAIT
        notification.save()

        result = serialize_items_from_order(self.order)

        self.assertTrue(result[0]["is_done"])

    def test_is_done_false_when_notification_status_prepare(self):
        baker.make(
            "order.OrderItem",
            order=self.order,
            name_snapshot="Salad",
            price_snapshot="8.00",
        )

        result = serialize_items_from_order(self.order)

        self.assertFalse(result[0]["is_done"])

    @patch("consumers.serializers.get_status_notification", return_value=None)
    def test_is_done_false_when_notification_missing(self, mock_get_status):
        baker.make(
            "order.OrderItem",
            order=self.order,
            name_snapshot="Gofr",
            price_snapshot="12.00",
        )

        result = serialize_items_from_order(self.order)

        self.assertFalse(result[0]["is_done"])
        mock_get_status.assert_called_once()

    def test_includes_additions_in_name_snapshot(self):
        item = baker.make(
            "order.OrderItem",
            order=self.order,
            name_snapshot="Gofr",
            price_snapshot="12.00",
        )
        baker.make(
            "order.OrderItemAddition",
            order_item=item,
            name_snapshot="Nutella",
            price_snapshot="3.00",
        )

        result = serialize_items_from_order(self.order)

        self.assertIn("Nutella", result[0]["name_snapshot"])


class SerializeOrderTests(TestCase):
    def setUp(self):
        self.user = baker.make("auth.User", username="adam")
        self.worker = baker.make("worker.Worker", user=self.user)
        self.bill = baker.make("order.Bill", service=self.worker)

    def test_serializes_order_with_all_fields(self):
        table = baker.make("service.Table", name="5")
        self.bill.table.add(table)
        order = baker.make(
            "order.Order",
            bill=self.bill,
            status=StatusOrder.ORDER,
            category=Location.KITCHEN,
        )

        result = serialize_order(order)

        self.assertEqual(result["id"], order.pk)
        self.assertEqual(result["sender"], "adam")
        self.assertEqual(result["table"], "5")
        self.assertEqual(result["status"], StatusOrder.ORDER)
        self.assertIn("order_items", result)
        self.assertIn("created_at", result)

    def test_created_at_is_formatted_string(self):
        order = baker.make("order.Order", bill=self.bill)

        result = serialize_order(order)

        # Should be formatted as YYYY-MM-DD HH:MM:SS
        self.assertEqual(len(result["created_at"]), 19)
        self.assertIn("-", result["created_at"])
        self.assertIn(":", result["created_at"])

    def test_order_items_included_in_serialization(self):
        order = baker.make("order.Order", bill=self.bill)
        baker.make(
            "order.OrderItem",
            order=order,
            name_snapshot="Pizza",
            price_snapshot="25.00",
            quantity=1,
        )

        result = serialize_order(order)

        self.assertEqual(len(result["order_items"]), 1)
        self.assertEqual(result["order_items"][0]["name_snapshot"], "Pizza")

    def test_multiple_tables_joined_with_comma(self):
        table1 = baker.make("service.Table", name="1")
        table2 = baker.make("service.Table", name="2")
        self.bill.table.add(table1, table2)
        order = baker.make("order.Order", bill=self.bill)

        result = serialize_order(order)

        self.assertIn("1", result["table"])
        self.assertIn("2", result["table"])
