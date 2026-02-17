from unittest.mock import patch

from django.test import TestCase

from order.factories import OrderMixinFactory
from order.queries import get_order


class TestGetOrder(OrderMixinFactory, TestCase):
    def setUp(self):
        self.main_order = self.make_order()

    def test_get_order(self):
        self.assertEqual(get_order(self.main_order.id), self.main_order)

    @patch("order.queries.logger.error", return_value=None)
    def test_should_not_find_order(self, mock_error):
        self.assertIsNone(get_order(self.main_order.pk + 1))
