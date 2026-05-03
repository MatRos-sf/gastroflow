from consumers.base import BaseConsumer, BaseNotificationConsumer
from menu.models import Location


class BarOrderConsumer(BaseConsumer):
    GROUP_NAME = "bar_orders"
    CATEGORY = Location.BAR


class OrderConsumer(BaseConsumer):
    GROUP_NAME = "kitchen_orders"
    CATEGORY = Location.KITCHEN


class NotificationConsumer(BaseNotificationConsumer):
    GROUP_NAME = "notifications"
