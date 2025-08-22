from base_consumers import BaseConsumer
from menu.models import Location


class BarOrderConsumer(BaseConsumer):
    GROUP_NAME = "bar_orders"
    CATEGORY = Location.BAR
