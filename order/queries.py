from datetime import timedelta
from logging import getLogger
from typing import Any

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


def get_orders_display_data(
    orders: QuerySet[Order], include_separator: bool = True
) -> tuple[list[dict[str, Any]], timedelta, bool]:
    """
    Build display data for a bill's orders.

    Args:
        orders: Prefetched queryset of orders with their items and additions.
        include_separator: If True, inserts a separator row before each order's items.

    Returns:
        A tuple of (items list, total preparing time, all orders ready flag).
    """
    items: list[dict] = []
    order_statuses: list[bool] = []
    preparing_time: list[timedelta] = []
    for order in orders:
        if include_separator:
            items.append(
                {"order": order.pk, "status": order.status, "category": order.category}
            )

        order_statuses.append(order.status == StatusOrder.READY)
        if order.readied_at:
            preparing_time.append(order.readied_at - order.created_at)

        for item in order.order_items.all():
            name = item.name_snapshot + (f" {item.note}" if item.note else "")
            items.append(
                {
                    "pk": item.pk,
                    "name": name,
                    "quantity": item.quantity,
                    "line_subtotal": item.line_subtotal,
                    "additions": [
                        {
                            "name": a.name_snapshot,
                            "line_subtotal": a.line_subtotal,
                        }
                        for a in item.order_item_additions.all()
                    ],
                }
            )

    all_orders_ready = all(order_statuses) if order_statuses else False
    return items, sum(preparing_time, timedelta()), all_orders_ready
