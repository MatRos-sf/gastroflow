from abc import ABC, abstractmethod
from datetime import datetime

from django.db.models import (
    Aggregate,
    Avg,
    Case,
    Count,
    DurationField,
    ExpressionWrapper,
    F,
    IntegerField,
    Q,
    Sum,
    When,
)

from order.models import (
    Bill,
    Location,
    Order,
    OrderItem,
    PaymentMethod,
    StatusBill,
    StatusOrder,
)
from tools.data_set import BillSummary, SummaryProtocol


class ReportCalculator(ABC):
    """Base class for report calculators."""

    name = "bill_status"
    frontend_info = None

    def filter_dates(
        self, qs, from_date: datetime | None = None, to_date: datetime | None = None
    ):
        raise NotImplementedError("This method should be implemented by subclasses")

    @abstractmethod
    def calculate(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        **kwargs
    ):
        raise NotImplementedError("This method should be implemented by subclasses")


class CountBillStatus(ReportCalculator):
    """Calculates the number of bills with each status between two dates."""

    name = "bills_status"

    def filter_dates(
        self, qs, from_date: datetime | None = None, to_date: datetime | None = None
    ):
        """
        None, None -> all
        date, None -> particular date
        date, date -> particular date range
        None, date -> Not supported
        """
        if not from_date and not to_date:
            return qs
        elif from_date and not to_date:
            return qs.filter(created_at__date=from_date)
        elif from_date and to_date:
            return qs.filter(created_at__range=(from_date, to_date))
        else:
            raise ValueError("Invalid date range")

    def calculate(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        **kwargs
    ):
        qs = Bill.objects
        qs = self.filter_dates(qs, from_date, to_date)

        return qs.aggregate(
            opened=Count(
                Case(When(status=StatusBill.OPEN, then=1), output_field=IntegerField())
            ),
            closed=Count(
                Case(
                    When(status=StatusBill.CLOSED, then=1), output_field=IntegerField()
                )
            ),
            pay_by_card=Count(
                Case(
                    When(payment_method=PaymentMethod.CARD, then=1),
                    output_field=IntegerField(),
                )
            ),
            pay_by_cash=Count(
                Case(
                    When(payment_method=PaymentMethod.CASH, then=1),
                    output_field=IntegerField(),
                )
            ),
            guest_count=Sum("guest_count", default=0),
            not_printed=Count(
                Case(When(is_printed=False, then=1), output_field=IntegerField())
            ),
        )


class OrderItemsQuantity(ReportCalculator):
    """Calculate the nameber of order items between two dates."""

    name = "order_item_quantity"
    frontend_info = "Liczba zamówień nie wliczając dodatków do zamówienia"

    def sum_quantity(self) -> Aggregate:
        return Sum("quantity", default=0)

    def sum_quantity_for_category(self, category: Location) -> Aggregate:
        return Sum(
            Case(
                When(order__category=category, then=F("quantity")),
                default=0,
                output_field=IntegerField(),
            )
        )

    def sum_quantity_not_ready_for_category(self, category: Location) -> Aggregate:
        return Sum(
            Case(
                When(
                    Q(order__category=category) & ~Q(order__status=StatusOrder.READY),
                    then=F("quantity"),
                ),
                default=0,
                output_field=IntegerField(),
            )
        )

    def filter_dates(
        self, qs, from_date: datetime | None = None, to_date: datetime | None = None
    ):
        """
        only ready orders
        None, None -> all
        date, None -> particular date
        date, date -> particular date range
        None, date -> Not supported
        """
        # qs = qs.filter(order__status=StatusOrder.READY)

        if not from_date and not to_date:
            return qs
        elif from_date and not to_date:
            return qs.filter(order__created_at__date=from_date)
        elif from_date and to_date:
            return qs.filter(order__created_at__range=(from_date, to_date))
        else:
            raise ValueError("Invalid date range")

    def calculate(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        **kwargs
    ):
        """
        Returns a dict with:
            * total: total number of order items
            * kitchen: number of order items in kitchen
            * bar: number of order items in bar
        """
        items_qs = OrderItem.objects.exclude(order__status=StatusOrder.CANCELED).all()
        items_qs = self.filter_dates(items_qs, from_date, to_date)

        return items_qs.aggregate(
            total=self.sum_quantity(),
            sum_kitchen=self.sum_quantity_for_category(Location.KITCHEN),
            sum_bar=self.sum_quantity_for_category(Location.BAR),
            not_ready_kitchen=self.sum_quantity_not_ready_for_category(
                Location.KITCHEN
            ),
            not_ready_bar=self.sum_quantity_not_ready_for_category(Location.BAR),
        )


class BillSummaryCalculator(ReportCalculator):
    name = "bill_summary"

    def __init__(self, summarizer: SummaryProtocol = BillSummary):
        self.summarizer = summarizer

    def filter_dates(
        self, qs, from_date: datetime | None = None, to_date: datetime | None = None
    ):
        pass

    def calculate(self, from_date, to_date, **kwargs):
        qs = (
            Bill.objects.filter(created_at__range=(from_date, to_date))
            .prefetch_related(
                "orders__order_items",
                "orders__order_items__order_item_additions",
                "service__user",
            )
            .values(
                "id",
                "payment_method",
                "discount",
                "service__user__username",
                "guest_count",
                "orders__order_items__id",
                "orders__order_items__price_snapshot",
                "orders__order_items__quantity",
                "orders__order_items__order_item_additions__pk",
                "orders__order_items__order_item_additions__price_snapshot",
            )
            .all()
        )
        summary_instance = self.summarizer.parse_from_qs(qs)
        return summary_instance.summary()


class AvgPreparationTime(ReportCalculator):
    """Calculate average preparation time per location."""

    name = "avg_preparation_time"

    def filter_dates(
        self, qs, from_date: datetime | None = None, to_date: datetime | None = None
    ):
        if not from_date and not to_date:
            return qs
        elif from_date and not to_date:
            return qs.filter(created_at__date=from_date)
        elif from_date and to_date:
            return qs.filter(created_at__range=(from_date, to_date))
        else:
            raise ValueError("Invalid date range")

    def _avg_for_location(self, qs, location: Location):
        return (
            qs.filter(category=location, readied_at__isnull=False)
            .annotate(
                preparing_time=ExpressionWrapper(
                    F("readied_at") - F("created_at"), output_field=DurationField()
                )
            )
            .aggregate(avg=Avg("preparing_time"))["avg"]
        )

    def calculate(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        **kwargs
    ):
        qs = Order.objects.exclude(status=StatusOrder.CANCELED)
        qs = self.filter_dates(qs, from_date, to_date)

        return {
            "kitchen": self._avg_for_location(qs, Location.KITCHEN),
            "bar": self._avg_for_location(qs, Location.BAR),
        }


CALCULATOR_COLLECTION = [
    CountBillStatus(),
    # OrderItemsQuantity(),
    # BillSummaryCalculator(),
]

CALCULATOR_BASIC = [CountBillStatus(), OrderItemsQuantity(), AvgPreparationTime()]
