from datetime import datetime
from decimal import Decimal
from typing import TypedDict, Unpack

from model_bakery import baker

from menu.models import Item
from order.models import Order, OrderItem, OrderItemStatus


class OrderItemKwargs(TypedDict, total=False):
    _quantity: int
    order: Order
    menu_item: Item
    name_snapshot: str
    price_snapshot: Decimal
    note: str
    status: OrderItemStatus
    created_at: datetime
    started_at: datetime
    finished_at: datetime
    quantity: int


class OrderItemMixinFactory:
    def make_order_item(self, **kwargs: Unpack[OrderItemKwargs]) -> OrderItem:
        return baker.make(OrderItem, **kwargs)

    def make_order_item_with_additions(
        self, addition_count: int = 1, **kwargs: Unpack[OrderItemKwargs]
    ) -> OrderItem:
        order_item = baker.make(OrderItem, **kwargs)
        baker.make(
            "order.OrderItemAddition",
            order_item=order_item,
            _quantity=addition_count,
        )
        return order_item
