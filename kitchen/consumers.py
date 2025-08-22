from base_consumers import BaseConsumer
from menu.models import Location


class OrderConsumer(BaseConsumer):
    GROUP_NAME = "kitchen_orders"
    CATEGORY = Location.KITCHEN
