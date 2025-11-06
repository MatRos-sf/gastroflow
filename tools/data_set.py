from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Protocol
from warnings import warn


class SummaryProtocol(Protocol):
    def summary(self) -> dict[str, Decimal]:
        ...

    @classmethod
    def parse_from_qs(cls, raw_data):
        ...


class PrepaymentMethodEnum(StrEnum):
    CARD = "karta"
    CASH = "gotówka"


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
        return sum([bill.revenue for bill in self.bills.values()]) or Decimal(0)

    def count_revenue_by_group(self) -> dict[str, Decimal]:
        """Return revenue grouped by payment method"""
        result = {}
        for method in PrepaymentMethodEnum:
            if method == PrepaymentMethodEnum.CARD:
                m = "revenue_card"
            else:
                m = "revenue_cash"
            _sum = sum(
                bill.revenue
                for bill in self.bills.values()
                if bill.payment_method == method
            )
            result[m] = _sum or Decimal(0)
        return result

    def summary(self) -> dict[str, Decimal]:
        """Return summary of revenue without discount"""
        revenue = self.count_revenue_by_group()
        revenue["revenue"] = self.count_revenue()

        assert abs(
            revenue["revenue"] - (revenue["revenue_cash"] + revenue["revenue_card"])
        ) < Decimal(
            "0.01"
        ), "Total revenue does not match the sum of cash an card revenue"

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
                    order_items={},
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
                warn("Order item pk not found")
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
