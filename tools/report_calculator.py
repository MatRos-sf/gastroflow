from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import (
    Aggregate,
    Avg,
    Case,
    Count,
    DecimalField,
    DurationField,
    ExpressionWrapper,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    When,
)
from django.db.models.functions import Coalesce, ExtractHour
from django.utils import timezone

from order.models import (
    Bill,
    Location,
    Order,
    OrderItem,
    OrderItemAddition,
    PaymentMethod,
    StatusBill,
    StatusOrder,
)
from worker.models import WorkTime


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
        **kwargs,
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
        **kwargs,
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
        **kwargs,
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


class BillEarnCalculator(ReportCalculator):
    name = "bill_earn"
    helper_text = "Bill earn is calculated only by closed bills"

    def filter_dates(
        self, qs, from_date: datetime | None = None, to_date: datetime | None = None
    ):
        if not from_date and not to_date:
            return qs
        elif from_date and not to_date:
            return qs.filter(closed_at__date=from_date)
        elif from_date and to_date:
            return qs.filter(closed_at__range=(from_date, to_date))
        else:
            raise ValueError("Invalid date range")

    def calculate(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        **kwargs,
    ):
        bill_qs = Bill.objects.filter(status=StatusBill.CLOSED)
        bill_qs = self.filter_dates(bill_qs, from_date, to_date)

        items_subquery = (
            OrderItem.objects.filter(order__bill=OuterRef("pk"))
            .values("order__bill")
            .annotate(total=Sum("line_subtotal"))
            .values("total")
        )

        additions_subquery = (
            OrderItemAddition.objects.filter(order_item__order__bill=OuterRef("pk"))
            .values("order_item__order__bill")
            .annotate(total=Sum("line_subtotal"))
            .values("total")
        )

        decimal_field = DecimalField(max_digits=12, decimal_places=2)

        bill_qs = (
            bill_qs.annotate(
                items_total=Coalesce(
                    Subquery(items_subquery, output_field=decimal_field),
                    Decimal("0.00"),
                ),
                additions_total=Coalesce(
                    Subquery(additions_subquery, output_field=decimal_field),
                    Decimal("0.00"),
                ),
            )
            .annotate(
                bill_earn=ExpressionWrapper(
                    (F("items_total") + F("additions_total"))
                    * (100 - F("discount"))
                    / 100,
                    output_field=decimal_field,
                ),
            )
            .annotate(
                bill_earn_no_print=Case(
                    When(is_printed=False, then=F("bill_earn")),
                    default=Decimal("0.00"),
                    output_field=decimal_field,
                ),
                bill_earn_print=Case(
                    When(is_printed=True, then=F("bill_earn")),
                    default=Decimal("0.00"),
                    output_field=decimal_field,
                ),
                bill_pay_by_card=Case(
                    When(payment_method=PaymentMethod.CARD, then=F("bill_earn")),
                    default=Decimal("0.00"),
                    output_field=decimal_field,
                ),
                bill_pay_by_cash=Case(
                    When(payment_method=PaymentMethod.CASH, then=F("bill_earn")),
                    default=Decimal("0.00"),
                    output_field=decimal_field,
                ),
            )
        )
        result = bill_qs.aggregate(
            total_earn=Sum("bill_earn", default=Decimal("0.00")),
            total_no_print=Sum("bill_earn_no_print", default=Decimal("0.00")),
            total_print=Sum("bill_earn_print", default=Decimal("0.00")),
            total_card=Sum("bill_pay_by_card", default=Decimal("0.00")),
            total_cash=Sum("bill_pay_by_cash", default=Decimal("0.00")),
        )
        result["total_earn"] = result["total_earn"].quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return result


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
        **kwargs,
    ):
        qs = Order.objects.exclude(status=StatusOrder.CANCELED)
        qs = self.filter_dates(qs, from_date, to_date)

        return {
            "kitchen": self._avg_for_location(qs, Location.KITCHEN),
            "bar": self._avg_for_location(qs, Location.BAR),
        }


class WaiterStatsCalculator(ReportCalculator):
    """Per-waiter stats: number of closed bills and total guests served."""

    name = "waiter_stats"

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

    def calculate(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        **kwargs,
    ):
        qs = Bill.objects.filter(status=StatusBill.CLOSED, waiter__isnull=False)
        qs = self.filter_dates(qs, from_date, to_date)

        return list(
            qs.values("waiter__id", "waiter__first_name", "waiter__last_name")
            .annotate(
                bill_count=Count("id"),
                guest_count=Sum("guest_count"),
            )
            .order_by("-bill_count")
        )


class WorkerSalaryCalculator(ReportCalculator):
    """Per-worker salary for a given day based on WorkTime records.

    If a worker has not finished their shift yet (finish_time is None),
    the calculation uses the current time as the end of the shift.
    """

    name = "worker_salary"

    def filter_dates(
        self, qs, from_date: datetime | None = None, to_date: datetime | None = None
    ):
        if not from_date and not to_date:
            return qs
        elif from_date and not to_date:
            return qs.filter(start_time__date=from_date)
        elif from_date and to_date:
            return qs.filter(start_time__date__range=(from_date, to_date))
        else:
            raise ValueError("Invalid date range")

    def calculate(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        **kwargs,
    ):
        qs = WorkTime.objects.filter(worker__isnull=False).select_related("worker")
        qs = self.filter_dates(qs, from_date, to_date)

        now = timezone.now()
        worker_data: dict[int, dict] = {}

        for wt in qs:
            finish = wt.finish_time or now
            duration = finish - wt.start_time
            hours = Decimal(str(duration.total_seconds() / 3600))
            earn = (hours * wt.salary_snapshot).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            if wt.worker_id not in worker_data:
                worker_data[wt.worker_id] = {
                    "name": str(wt.worker),
                    "position": wt.worker.position,
                    "total_earn": Decimal("0.00"),
                    "hours_worked": timedelta(),
                    "is_working": False,
                }

            worker_data[wt.worker_id]["total_earn"] += earn
            worker_data[wt.worker_id]["hours_worked"] += duration
            if wt.finish_time is None:
                worker_data[wt.worker_id]["is_working"] = True

        return {"workers": sorted(worker_data.values(), key=lambda w: w["name"])}


class HourlyDistributionCalculator(ReportCalculator):
    """Number of closed bills per hour of the day."""

    name = "hourly_distribution"

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

    def calculate(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        **kwargs,
    ):
        qs = Bill.objects.filter(status=StatusBill.CLOSED)
        qs = self.filter_dates(qs, from_date, to_date)

        return list(
            qs.annotate(hour=ExtractHour("created_at"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )


CALCULATOR_COLLECTION = [
    CountBillStatus(),
    BillEarnCalculator(),
    OrderItemsQuantity(),
    AvgPreparationTime(),
    WaiterStatsCalculator(),
    WorkerSalaryCalculator(),
    HourlyDistributionCalculator(),
]

CALCULATOR_BASIC = [CountBillStatus(), OrderItemsQuantity(), AvgPreparationTime()]
