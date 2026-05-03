from decimal import Decimal
from typing import TypedDict, Unpack

from model_bakery import baker

from order.models import OrderItem, OrderItemAddition


class OrderItemAdditionKwargs(TypedDict, total=False):
    _quantity: int
    order_item: OrderItem
    name_snapshot: str
    price_snapshot: Decimal
    quantity: int


class OrderItemAdditionMixinFactory:
    def make_addition(
        self, **kwargs: Unpack[OrderItemAdditionKwargs]
    ) -> OrderItemAddition:
        return baker.make(OrderItemAddition, **kwargs)
