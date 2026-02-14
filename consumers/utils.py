import logging
from typing import Optional

from order.models import NotificationStatus, OrderItem

logger = logging.getLogger(__name__)


def dish_is_done(notification_status: Optional[NotificationStatus]) -> bool:
    return notification_status in [NotificationStatus.WAIT, NotificationStatus.SERVE]


def get_status_notification(item: OrderItem) -> Optional[NotificationStatus]:
    try:
        return item.notification.status
    except OrderItem.notification.RelatedObjectDoesNotExist:
        logger.warning(f"Notification not found for item {item.id}")
        return None
