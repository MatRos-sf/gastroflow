from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from consumers.serializers import (
    serialize_additions_from_order_item,
    serialize_items_from_order,
    serialize_order,
)
from order.models import OrderItemStatus


class SerializeAdditionsUnitTest(TestCase):
    def test_returns_empty_list_for_no_additions(self):
        result = serialize_additions_from_order_item([])

        self.assertEqual(result, [])

    def test_serializes_single_addition(self):
        addition = MagicMock(name_snapshot="Nutella", quantity=2)

        result = serialize_additions_from_order_item([addition])

        self.assertEqual(result, [{"name_snapshot": "Nutella", "quantity": 2}])

    def test_serializes_multiple_additions(self):
        additions = [
            MagicMock(name_snapshot="Nutella", quantity=1),
            MagicMock(name_snapshot="Syrop", quantity=3),
        ]

        result = serialize_additions_from_order_item(additions)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name_snapshot"], "Nutella")
        self.assertEqual(result[1]["name_snapshot"], "Syrop")

    def test_returns_only_name_snapshot_and_quantity(self):
        addition = MagicMock(name_snapshot="Bita śmietana", quantity=1)

        result = serialize_additions_from_order_item([addition])

        self.assertSetEqual(set(result[0].keys()), {"name_snapshot", "quantity"})


class SerializeItemsFromOrderUnitTest(TestCase):
    def _make_item(
        self,
        name="Pizza",
        quantity=1,
        note="",
        status=OrderItemStatus.WAITING,
        additions=None,
    ):
        item = MagicMock()
        item.id = 1
        item.name_snapshot = name
        item.quantity = quantity
        item.note = note
        item.status = status
        item.order_item_additions.all.return_value = additions or []
        return item

    def test_uses_prefetched_items_when_available(self):
        order = MagicMock()
        order._prefetched_items = [self._make_item("Pizza")]

        result = serialize_items_from_order(order)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name_snapshot"], "Pizza")
        order.order_items.order_by.assert_not_called()

    def test_falls_back_to_db_query_when_no_prefetch(self):
        order = MagicMock(spec=["order_items"])  # no _prefetched_items attr
        order.order_items.order_by.return_value.all.return_value = [
            self._make_item("Pasta")
        ]

        result = serialize_items_from_order(order)

        self.assertEqual(result[0]["name_snapshot"], "Pasta")
        order.order_items.order_by.assert_called_once_with("name_snapshot")

    def test_returns_empty_list_when_no_items(self):
        order = MagicMock()
        order._prefetched_items = []

        result = serialize_items_from_order(order)

        self.assertEqual(result, [])

    def test_serializes_all_item_fields(self):
        item = self._make_item(
            "Zupa", quantity=3, note="bez soli", status=OrderItemStatus.READY
        )
        order = MagicMock()
        order._prefetched_items = [item]

        result = serialize_items_from_order(order)

        self.assertEqual(result[0]["id"], item.id)
        self.assertEqual(result[0]["name_snapshot"], "Zupa")
        self.assertEqual(result[0]["quantity"], 3)
        self.assertEqual(result[0]["note"], "bez soli")
        self.assertEqual(result[0]["status"], OrderItemStatus.READY)

    def test_includes_serialized_additions(self):
        addition = MagicMock(name_snapshot="Parmezan", quantity=1)
        item = self._make_item(additions=[addition])
        order = MagicMock()
        order._prefetched_items = [item]

        result = serialize_items_from_order(order)

        self.assertEqual(
            result[0]["additions"], [{"name_snapshot": "Parmezan", "quantity": 1}]
        )

    def test_returns_empty_additions_when_none(self):
        order = MagicMock()
        order._prefetched_items = [self._make_item(additions=[])]

        result = serialize_items_from_order(order)

        self.assertEqual(result[0]["additions"], [])


class SerializeOrderUnitTest(TestCase):
    def _make_order(self, sender="Jan Kowalski", table="3", note=None, status="order"):
        order = MagicMock()
        order.pk = 42
        order.status = status
        order.bill.waiter.__str__.return_value = sender
        order.bill.str_tables.return_value = table
        order.bill.note = note
        order.created_at = timezone.now()
        return order

    @patch("consumers.serializers.serialize_items_from_order", return_value=[])
    def test_returns_all_expected_keys(self, _):
        result = serialize_order(self._make_order())

        self.assertSetEqual(
            set(result.keys()),
            {"id", "sender", "table", "note", "status", "order_items", "created_at"},
        )

    @patch("consumers.serializers.serialize_items_from_order", return_value=[])
    def test_id_is_order_pk(self, _):
        result = serialize_order(self._make_order())

        self.assertEqual(result["id"], 42)

    @patch("consumers.serializers.serialize_items_from_order", return_value=[])
    def test_sender_is_str_of_waiter(self, _):
        result = serialize_order(self._make_order(sender="Anna Nowak"))

        self.assertEqual(result["sender"], "Anna Nowak")

    @patch("consumers.serializers.serialize_items_from_order", return_value=[])
    def test_table_comes_from_str_tables(self, _):
        result = serialize_order(self._make_order(table="7"))

        self.assertEqual(result["table"], "7")

    @patch("consumers.serializers.serialize_items_from_order", return_value=[])
    def test_note_passed_through(self, _):
        result = serialize_order(self._make_order(note="okno od ulicy"))

        self.assertEqual(result["note"], "okno od ulicy")

    @patch("consumers.serializers.serialize_items_from_order", return_value=[])
    def test_created_at_is_formatted_string(self, _):
        result = serialize_order(self._make_order())

        self.assertRegex(result["created_at"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

    @patch("consumers.serializers.serialize_items_from_order")
    def test_order_items_delegates_to_serialize_items(self, mock_serialize_items):
        mock_serialize_items.return_value = [{"id": 1}]
        order = self._make_order()

        result = serialize_order(order)

        mock_serialize_items.assert_called_once_with(order)
        self.assertEqual(result["order_items"], [{"id": 1}])
