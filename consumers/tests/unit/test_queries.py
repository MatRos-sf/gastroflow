from unittest.mock import MagicMock, patch

from django.test import TestCase

from consumers.queries import _get_unserved_orders
from menu.models import Location
from order.models import StatusOrder


class GetUnservedOrdersUnitTest(TestCase):
    def _mock_chain(self, return_value):
        """Returns a mock that survives .filter().select_related().prefetch_related().order_by()."""
        terminal = MagicMock()
        terminal.__iter__ = MagicMock(return_value=iter(return_value))
        chain = MagicMock()
        chain.filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = (
            terminal
        )
        return chain

    @patch("consumers.queries.serialize_order")
    @patch("consumers.queries.Order.objects")
    def test_filters_by_unserved_statuses(self, mock_objects, mock_serialize):
        mock_objects.filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = (
            []
        )

        _get_unserved_orders(Location.KITCHEN)

        mock_objects.filter.assert_called_once_with(
            status__in=[StatusOrder.ORDER, StatusOrder.PREPARING],
            category=Location.KITCHEN,
        )

    @patch("consumers.queries.serialize_order")
    @patch("consumers.queries.Order.objects")
    def test_orders_by_created_at(self, mock_objects, mock_serialize):
        terminal = MagicMock()
        terminal.__iter__ = MagicMock(return_value=iter([]))
        mock_objects.filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = (
            terminal
        )

        _get_unserved_orders(Location.KITCHEN)

        mock_objects.filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.assert_called_once_with(
            "created_at"
        )

    @patch("consumers.queries.serialize_order")
    @patch("consumers.queries.Order.objects")
    def test_calls_serialize_order_for_each_result(self, mock_objects, mock_serialize):
        order1, order2 = MagicMock(), MagicMock()
        mock_objects.filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [
            order1,
            order2,
        ]
        mock_serialize.side_effect = lambda o: {"id": id(o)}

        _get_unserved_orders(Location.KITCHEN)

        self.assertEqual(mock_serialize.call_count, 2)
        mock_serialize.assert_any_call(order1)
        mock_serialize.assert_any_call(order2)

    @patch("consumers.queries.serialize_order")
    @patch("consumers.queries.Order.objects")
    def test_returns_serialized_list(self, mock_objects, mock_serialize):
        order = MagicMock()
        mock_objects.filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = [
            order
        ]
        mock_serialize.return_value = {"id": 1, "status": "order"}

        result = _get_unserved_orders(Location.KITCHEN)

        self.assertEqual(result, [{"id": 1, "status": "order"}])

    @patch("consumers.queries.serialize_order")
    @patch("consumers.queries.Order.objects")
    def test_returns_empty_list_when_no_orders(self, mock_objects, mock_serialize):
        mock_objects.filter.return_value.select_related.return_value.prefetch_related.return_value.order_by.return_value = (
            []
        )

        result = _get_unserved_orders(Location.KITCHEN)

        self.assertEqual(result, [])
        mock_serialize.assert_not_called()
