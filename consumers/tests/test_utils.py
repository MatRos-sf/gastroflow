from django.test import TestCase
from model_bakery import baker
from parameterized import parameterized

from consumers.utils import dish_is_done, get_status_notification
from order.models import NotificationStatus


class DishIsDoneTests(TestCase):
    @parameterized.expand([NotificationStatus.WAIT, NotificationStatus.SERVE])
    def test_returns_true_for_done_status(self, status):
        self.assertTrue(dish_is_done(status))

    @parameterized.expand([NotificationStatus.PREPARE])
    def test_returns_false_for_prepare_status(self, status):
        self.assertFalse(dish_is_done(status))

    def test_returns_false_for_none(self):
        self.assertFalse(dish_is_done(None))


class GetStatusNotificationTests(TestCase):
    def setUp(self):
        self.worker = baker.make("worker.Worker")

    def make_dummy_bill_with_order(self, worker=None, bill=None):
        if not bill:
            bill = baker.make("order.Bill", service=worker or self.worker)

        order = baker.make("order.Order", bill=bill)
        item = baker.make("order.OrderItem", order=order)

        return bill, order, item

    def test_returns_notification_status_when_exists(self):
        bill, order, item = self.make_dummy_bill_with_order()

        notification = item.notification
        notification.status = NotificationStatus.WAIT
        notification.save()

        result = get_status_notification(item)

        self.assertEqual(result == NotificationStatus.WAIT)

    def test_returns_none_when_notification_does_not_exist(self):
        bill, order, item = self.make_dummy_bill_with_order()

        item.notification.delete()
        item.refresh_from_db()

        result = get_status_notification(item)

        self.assertIsNone(result)
