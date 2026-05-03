from unittest.mock import patch

from django.test import TestCase
from model_bakery import baker

from consumers.utils import get_status_notification
from order.models import NotificationStatus


class GetStatusNotificationTests(TestCase):
    def setUp(self):
        self.worker = baker.make("worker.Worker")

    def make_dummy_bill_with_order(self, worker=None, bill=None):
        if not bill:
            bill = baker.make("order.Bill", waiter=worker or self.worker)

        order = baker.make("order.Order", bill=bill)
        item = baker.make("order.OrderItem", order=order)

        return bill, order, item

    def test_returns_notification_status_when_exists(self):
        bill, order, item = self.make_dummy_bill_with_order()

        notification = item.notification
        notification.status = NotificationStatus.WAITING_TO_READ
        notification.save()
        result = get_status_notification(item)

        self.assertEqual(result, NotificationStatus.WAITING_TO_READ)

    @patch("consumers.utils.logger.warning", return_value=None)
    def test_returns_none_when_notification_does_not_exist(self, mock_warning):
        bill, order, item = self.make_dummy_bill_with_order()

        item.notification.delete()
        item.refresh_from_db()

        result = get_status_notification(item)

        self.assertIsNone(result)
