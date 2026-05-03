from datetime import datetime
from typing import TypedDict, Unpack

from model_bakery import baker

from menu.models import Location
from order.models import Bill, Order, StatusOrder


class OrderKwargs(TypedDict, total=False):
    _quantity: int
    bill: Bill
    status: StatusOrder
    category: Location
    created_at: datetime
    preparing_at: datetime | None
    readied_at: datetime | None
    paid_at: datetime | None
    canceled_at: datetime | None


class OrderMixinFactory:
    def make_order(self, **kwargs: Unpack[OrderKwargs]) -> Order:
        return baker.make(Order, **kwargs)

    def make_kitchen_order(self, **kwargs: Unpack[OrderKwargs]) -> Order:
        kwargs.setdefault("category", Location.KITCHEN)
        return baker.make(Order, **kwargs)

    def make_bar_order(self, **kwargs: Unpack[OrderKwargs]) -> Order:
        kwargs.setdefault("category", Location.BAR)
        return baker.make(Order, **kwargs)

    def make_order_with_items(
        self, item_count: int = 2, **kwargs: Unpack[OrderKwargs]
    ) -> Order:
        order = baker.make(Order, **kwargs)
        baker.make("order.OrderItem", order=order, _quantity=item_count)
        return order
