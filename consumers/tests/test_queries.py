from asgiref.sync import async_to_sync
from django.test import TransactionTestCase
from model_bakery import baker

from consumers.queries import get_unserved_orders
from menu.models import Location
from order.models import StatusOrder


class GetUnservedOrdersTests(TransactionTestCase):
    def setUp(self):
        self.worker = baker.make("worker.Worker")
        self.bill = baker.make("order.Bill", service=self.worker)

    def _call(self, category):
        return async_to_sync(get_unserved_orders)(category)

    def test_returns_ordering_orders(self):
        baker.make(
            "order.Order",
            bill=self.bill,
            status=StatusOrder.ORDER,
            category=Location.KITCHEN,
        )

        result = self._call(Location.KITCHEN)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], StatusOrder.ORDER)

    def test_returns_preparing_orders(self):
        baker.make(
            "order.Order",
            bill=self.bill,
            status=StatusOrder.PREPARING,
            category=Location.KITCHEN,
        )

        result = self._call(Location.KITCHEN)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], StatusOrder.PREPARING)

    def test_excludes_ready_orders(self):
        baker.make(
            "order.Order",
            bill=self.bill,
            status=StatusOrder.READY,
            category=Location.KITCHEN,
        )

        result = self._call(Location.KITCHEN)

        self.assertEqual(len(result), 0)

    def test_excludes_paid_orders(self):
        baker.make(
            "order.Order",
            bill=self.bill,
            status=StatusOrder.PAID,
            category=Location.KITCHEN,
        )

        result = self._call(Location.KITCHEN)

        self.assertEqual(len(result), 0)

    def test_filters_by_category(self):
        baker.make(
            "order.Order",
            bill=self.bill,
            status=StatusOrder.ORDER,
            category=Location.KITCHEN,
        )
        baker.make(
            "order.Order",
            bill=self.bill,
            status=StatusOrder.ORDER,
            category=Location.BAR,
        )

        kitchen_result = self._call(Location.KITCHEN)
        bar_result = self._call(Location.BAR)

        self.assertEqual(len(kitchen_result), 1)
        self.assertEqual(len(bar_result), 1)

    def test_returns_empty_list_when_no_orders(self):
        result = self._call(Location.KITCHEN)

        self.assertEqual(result, [])
