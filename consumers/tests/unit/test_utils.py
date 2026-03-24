from unittest.mock import MagicMock, patch

from django.test import TestCase

from consumers.utils import get_status_notification
from order.models import NotificationStatus, OrderItem

_NotificationDoesNotExist = OrderItem.notification.RelatedObjectDoesNotExist


def _make_item_without_notification(item_id=99):
    class FakeItem:
        id = item_id

        @property
        def notification(self):
            raise _NotificationDoesNotExist()

    return FakeItem()


class GetStatusNotificationUnitTest(TestCase):
    def test_returns_status_when_notification_exists(self):
        item = MagicMock()
        item.notification.status = NotificationStatus.WAITING_TO_READ

        result = get_status_notification(item)

        self.assertEqual(result, NotificationStatus.WAITING_TO_READ)

    def test_returns_none_when_notification_does_not_exist(self):
        item = _make_item_without_notification()

        result = get_status_notification(item)

        self.assertIsNone(result)

    @patch("consumers.utils.logger")
    def test_logs_warning_when_notification_missing(self, mock_logger):
        item = _make_item_without_notification(item_id=99)

        get_status_notification(item)

        mock_logger.warning.assert_called_once_with(
            "Notification not found for item 99"
        )
