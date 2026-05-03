from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any, Protocol
from warnings import warn

REVENUE_TOLERANCE = Decimal("0.01")


class SummaryProtocol(Protocol):
    def summary(self) -> dict[str, Decimal]:
        ...

    @classmethod
    def parse_from_qs(cls, raw_data):
        ...


class PaymentMethodEnum(StrEnum):
    CARD = "card"
    CASH = "cash"


@dataclass
class AdditionData:
    pk: int
    price: Decimal


@dataclass
class ItemData:
    pk: int
    price: Decimal
    quantity: int
    additions: list[AdditionData]

    @property
    def total(self):
        """Total is count of item with additions. Also quantity increase amount of additions"""
        additions = sum(a.price * self.quantity for a in self.additions)
        return self.price * self.quantity + additions


@dataclass
class BillData:
    pk: int
    payment_method: str
    discount: int
    order_items: dict[int, ItemData]
    guest_count: int
    service_user: str

    @property
    def price(self):
        """Price without discount"""
        orders_sum = sum([item.total for item in self.order_items.values()])
        return orders_sum

    @property
    def revenue(self) -> Decimal:
        """Price with discount"""
        orders_sum = self.price
        return orders_sum * (Decimal(1) - Decimal(self.discount) / Decimal(100))


class BillSummary:
    def __init__(self, data: dict[int, BillData]):
        self.bills = data

    def __len__(self):
        return len(self.bills)

    def count_revenue(self) -> Decimal:
        return sum([bill.revenue for bill in self.bills.values()], start=Decimal(0))

    def count_guests(self) -> int:
        return sum([bill.guest_count for bill in self.bills.values()]) or 0

    def avg_per_plate(self, revenue: Decimal | None = None):
        """
        Calculate average revenue per guests

        Returns:
            Decimal: Average revenue divided by total number of guests.
                    Returns 0.00 if there are no guests.
        """
        if not revenue:
            revenue = self.count_revenue()
        number_of_guests = self.count_guests()
        if not number_of_guests:
            return Decimal("0.00")

        return (revenue / Decimal(number_of_guests)).quantize(Decimal("0.01"))

    def count_revenue_by_group(self) -> dict[str, Decimal]:
        """Return revenue grouped by payment method"""
        result = {}
        for payment_method in PaymentMethodEnum:
            if payment_method == PaymentMethodEnum.CARD:
                revenue_key = "revenue_card"
            else:
                revenue_key = "revenue_cash"
            total_revenue = sum(
                bill.revenue
                for bill in self.bills.values()
                if bill.payment_method == payment_method
            )
            result[revenue_key] = total_revenue or Decimal(0)
        return result

    def calculate_waiter_stats(self) -> dict[str, dict[str, int | Decimal]]:
        """
        Returns waiter stats.
        """
        result = {}
        for bill in self.bills.values():
            waiter_stats = result.get(
                bill.service_user, {"bills": 0, "revenue": Decimal("0.00")}
            )
            waiter_stats["bills"] += 1
            waiter_stats["revenue"] += bill.revenue
            result[bill.service_user] = waiter_stats
        return result

    def summary(self) -> dict[str, Any]:
        """Return summary of revenue without discount"""
        revenue = self.count_revenue_by_group()
        revenue["revenue"] = self.count_revenue()

        test_revenue = abs(
            revenue["revenue"] - (revenue["revenue_cash"] + revenue["revenue_card"])
        )

        if test_revenue > REVENUE_TOLERANCE:
            raise ValueError(
                f"Total revenue does not match the sum of cash an card revenue ({test_revenue})"
            )

        revenue["avg_per_plate"] = self.avg_per_plate(revenue["revenue"])
        revenue["guests"] = self.count_guests()
        revenue["waiter"] = self.calculate_waiter_stats()
        return revenue

    @classmethod
    def parse_from_qs(cls, raw_data):
        data: dict[int, BillData] = {}
        for datum in raw_data:
            bill_instance = data.get(datum["id"])
            if not bill_instance:
                bill_instance = BillData(
                    pk=datum["id"],
                    payment_method=datum["payment_method"],
                    discount=datum["discount"],
                    guest_count=datum["guest_count"],
                    order_items={},
                    service_user=datum.get("service__user__username", "Unknown"),
                )

            item_instance = bill_instance.order_items.get(
                datum["orders__order_items__id"]
            )
            if not item_instance:
                item_instance = ItemData(
                    pk=datum["orders__order_items__id"],
                    price=datum["orders__order_items__price_snapshot"],
                    quantity=datum["orders__order_items__quantity"],
                    additions=[],
                )

            order_item_pk = datum["orders__order_items__id"]
            if not order_item_pk:
                warn("Order item pk not found", FutureWarning)
                continue

            bill_instance.order_items[order_item_pk] = item_instance

            additions = datum.get("orders__order_items__order_item_additions__pk")
            if additions:
                item_instance.additions.append(
                    AdditionData(
                        pk=additions,
                        price=datum[
                            "orders__order_items__order_item_additions__price_snapshot"
                        ],
                    )
                )

            data[datum["id"]] = bill_instance

        return cls(data)
