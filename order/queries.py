import datetime
from datetime import timedelta
from decimal import Decimal
from logging import getLogger
from typing import Any

from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Prefetch, Q, QuerySet
from django.utils import timezone

from order.models import (
    Bill,
    Notification,
    NotificationStatus,
    Order,
    OrderItem,
    OrderItemAddition,
    OrderItemStatus,
    StatusBill,
    StatusOrder,
)
from service.models import Table
from service.queries import process_bill_closure

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


def get_recent_unread_notifications(limit: int = 3) -> list[dict]:
    qs = Notification.objects.filter(
        status=NotificationStatus.WAITING_TO_READ
    ).order_by("-created_at")[:limit]
    return [
        {"message": n.message, "notification_type": n.notification_type} for n in qs
    ]


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


def _build_paid_at_filter(
    from_date: datetime.date | None,
    to_date: datetime.date | None,
    field: str,
) -> Q:
    """Build a date filter Q object based on provided date range."""
    if from_date and to_date:
        return Q(**{f"{field}__date__range": (from_date, to_date)})
    if from_date:
        return Q(**{f"{field}__date": from_date})
    if to_date:
        return Q(**{f"{field}__date__lte": to_date})
    return Q()


def get_order_items_detail(
    from_date: datetime.date | None,
    to_date: datetime.date | None,
) -> QuerySet:
    return (
        OrderItem.objects.filter(
            _build_paid_at_filter(from_date, to_date, "order__bill__paid_at"),
            order__bill__status__in=[StatusBill.CLOSED, StatusBill.CLOSED_AND_OCCUPIED],
        )
        .annotate(
            bill_pk=F("order__bill__pk"),
            paid_at=F("order__bill__paid_at"),
        )
        .values(
            "pk",
            "bill_pk",
            "name_snapshot",
            "quantity",
            "price_snapshot",
            "line_subtotal",
            "line_final_total",
            "paid_at",
        )
        .order_by("-paid_at")
    )


def get_order_additions_detail(
    from_date: datetime.date | None,
    to_date: datetime.date | None,
) -> QuerySet:
    return (
        OrderItemAddition.objects.filter(
            _build_paid_at_filter(
                from_date, to_date, "order_item__order__bill__paid_at"
            ),
            order_item__order__bill__status__in=[
                StatusBill.CLOSED,
                StatusBill.CLOSED_AND_OCCUPIED,
            ],
        )
        .annotate(
            bill_pk=F("order_item__order__bill__pk"),
            order_item_pk=F("order_item__pk"),
            paid_at=F("order_item__order__bill__paid_at"),
        )
        .values(
            "pk",
            "bill_pk",
            "order_item_pk",
            "name_snapshot",
            "quantity",
            "price_snapshot",
            "line_subtotal",
            "line_final_total",
            "paid_at",
        )
        .order_by("-paid_at")
    )


@transaction.atomic
def close_bill_process(
    bill: Bill, status: str, payment_method: str | None = None
) -> None:
    process_bill_closure(bill, status, payment_method)

    multiplier = Decimal(100 - bill.discount) / Decimal(100)
    expression_wrapper = ExpressionWrapper(
        F("line_subtotal") * multiplier,
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )

    OrderItem.objects.filter(order__bill=bill).update(
        line_final_total=expression_wrapper
    )

    OrderItemAddition.objects.filter(order_item__order__bill=bill).update(
        line_final_total=expression_wrapper
    )
