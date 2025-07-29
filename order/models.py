from django.db import models

from menu.models import Addition, Item


class StatusOrder(models.TextChoices):
    ORDER = "order", "ORDER"
    PREPARING = "preparing", "PREPARING"
    READY = "ready", "READY"
    PAID = "paid", "PAID"
    CANCELED = "canceled", "CANCELED"


class Order(models.Model):
    status = models.CharField(
        max_length=20,
        choices=StatusOrder.choices,
        default=StatusOrder.ORDER,
    )
    table = models.CharField(null=True, blank=True, max_length=20)

    # Date time fields
    created_at = models.DateTimeField(auto_now_add=True)
    readied_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} - Table {self.table if self.table else 'N/A'}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items"
    )
    menu_item = models.ForeignKey(Item, on_delete=models.CASCADE)
    name_snapshot = models.CharField(
        max_length=150, help_text="Name of dish with additions"
    )
    price_snapshot = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Price of dish when it was ordered"
    )
    note = models.TextField(null=True, blank=True, max_length=500)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.name_snapshot} x{self.quantity}"


class OrderItemAddition(models.Model):
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name="order_item_additions"
    )
    addition = models.ForeignKey(Addition, on_delete=models.CASCADE)
    name_snapshot = models.CharField(max_length=100)
    price_snapshot = models.DecimalField(max_digits=7, decimal_places=2)
