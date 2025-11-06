from abc import ABC, abstractmethod
from typing import Any

from django.db.models import Aggregate, Case, Count, F, IntegerField, Sum, When

from order.models import Bill, Location, OrderItem, PaymentMethod, StatusBill
from tools.data_set import BillSummary, SummaryProtocol


class ReportCalculator(ABC):
    """Base class for report calculators."""

    name = "bill_status"
    frontend_info = None

    @abstractmethod
    def calculate(self, from_date, to_date, **kwargs):
        raise NotImplementedError("This method should be implemented by subclasses")


class CountBillStatus(ReportCalculator):
    """Calculates the number of bills with each status between two dates."""

    name = "bills_status"

    def calculate(self, from_date, to_date, **kwargs):
        return Bill.objects.filter(created_at__range=(from_date, to_date)).aggregate(
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
                output_field=IntegerField(),
            )
        )

    def calculate(self, from_date, to_date, **kwargs) -> dict[str, Any]:
        """
        Returns a dict with:
            * total: total number of order items
            * kitchen: number of order items in kitchen
            * bar: number of order items in bar
        """
        items_qs = OrderItem.objects.filter(
            finished_at__range=(from_date, to_date)
        ).select_related("order")
        return items_qs.aggregate(
            total=self.sum_quantity(),
            kitchen=self.sum_quantity_for_category(Location.KITCHEN),
            bar=self.sum_quantity_for_category(Location.BAR),
        )


class BillSummaryCalculator(ReportCalculator):
    name = "bill_summary"

    def __init__(self, summarizer: SummaryProtocol = BillSummary):
        self.summarizer = summarizer

    def calculate(self, from_date, to_date, **kwargs):
        qs = (
            Bill.objects.filter(created_at__range=(from_date, to_date))
            .prefetch_related(
                "orders__order_items", "orders__order_items__order_item_additions"
            )
            .values(
                "id",
                "payment_method",
                "discount",
                "orders__order_items__id",
                "orders__order_items__price_snapshot",
                "orders__order_items__quantity",
                "orders__order_items__order_item_additions__pk",
                "orders__order_items__order_item_additions__price_snapshot",
            )
            .all()
        )
        self.summarizer.parse_from_qs(qs)
        return self.summarizer.summary()
