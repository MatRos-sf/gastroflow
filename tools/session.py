from dataclasses import dataclass

from menu.models import Location


@dataclass
class SessionInfo:
    cart: list
    tables: list
    waiter: int
    bill: int


def split_items_by_location(cart_items: list[dict]) -> tuple[list[dict], list[dict]]:
    """Separate cart_items to different location"""
    kitchen_items = [
        i for i in cart_items if i["preparation_location"] == Location.KITCHEN
    ]
    bar_items = [i for i in cart_items if i["preparation_location"] == Location.BAR]
    return kitchen_items, bar_items
