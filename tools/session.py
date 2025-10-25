from dataclasses import dataclass
from typing import Iterable

from django.http import HttpRequest

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


def clear_session(req: HttpRequest, session_field: Iterable) -> None:
    """
    Clear session variables given in session_field
    """
    for name in session_field:
        req.session.pop(name, None)
