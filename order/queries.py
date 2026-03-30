from logging import getLogger

from django.db import transaction
from django.db.models import Prefetch, Q, QuerySet
from django.utils import timezone

from order.models import (
    Bill,
    Notification,
    NotificationStatus,
    Order,
    OrderItem,
    OrderItemStatus,
    StatusOrder,
)
from service.models import Table

logger = getLogger(__name__)


def get_order(order_id: int) -> Order | None:
    try:
        return Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order with ID {order_id} does not exist.")
        return None


@transaction.atomic
def update_batch_order_items_status(order_id: int, status: OrderItemStatus) -> None:
    order = get_order(order_id)

    if not order:
        return

    order.status = status

    if status == StatusOrder.PREPARING:
        OrderItem.objects.filter(
            Q(order=order) & Q(status=OrderItemStatus.WAITING)
        ).update(
            status=OrderItemStatus.PREPARING,
            started_at=timezone.now(),
        )
        order.preparing_at = timezone.now()

    elif status == StatusOrder.READY:
        OrderItem.objects.filter(order=order).update(
            status=OrderItemStatus.READY,
        )
        order.finished_at = timezone.now()

    if status == StatusOrder.READY:
        order.readied_at = timezone.now()

    order.save()
    logger.info(f"Order with ID {order_id} was updated to {status}.")


def update_batch_notifications_status(
    notification_ids: list[int], status: NotificationStatus
) -> None:
    Notification.objects.filter(id__in=notification_ids).update(
        status=status, last_update=timezone.now()
    )


def get_bills_with_totals() -> QuerySet[Bill]:
    return Bill.objects.prefetch_related(
        "orders__order_items__order_item_additions",
        Prefetch("table", queryset=Table.objects.select_related("hall")),
    ).order_by("-created_at")
