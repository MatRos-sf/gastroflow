import logging
from typing import Optional

from order.models import NotificationStatus, OrderItem

logger = logging.getLogger(__name__)


def get_status_notification(item: OrderItem) -> Optional[NotificationStatus]:
    try:
        return item.notification.status
    except OrderItem.notification.RelatedObjectDoesNotExist:
        logger.warning(f"Notification not found for item {item.id}")
        return None
