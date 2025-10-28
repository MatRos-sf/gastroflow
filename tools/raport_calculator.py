from abc import ABC, abstractmethod
from typing import Any

from django.db.models import Aggregate, Case, Count, F, IntegerField, Sum, When

from order.models import Bill, Location, OrderItem, StatusBill


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
