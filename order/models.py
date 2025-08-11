from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.utils import timezone

from menu.models import Addition, CategoryOrder, Item
from service.models import Table


class StatusOrder(models.TextChoices):
    ORDER = "ordering", "ORDERING"
    PREPARING = "preparing", "PREPARING"
    READY = "ready", "READY"
    PAID = "paid", "PAID"
    CANCELED = "canceled", "CANCELED"


class StatusBill(models.TextChoices):
    OPEN = "open", "OPEN"
    CLOSED = "closed", "CLOSED"


class Bill(models.Model):
    table = models.ManyToManyField(Table, blank=True)
    status = models.CharField(
        max_length=10, choices=StatusBill.choices, default=StatusBill.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # Payment additional
    # is_cash
    # tip
    # given_money
    def __str__(self):
        return f"Bill {self.id} - Table {self.table or 'take-away'}"

    @property
    def total(self):
        raise NotImplementedError

    def close(self):
        self.status = StatusBill.CLOSED
        self.closed_at = timezone.now()
        self.save()

    def bill_summary_view(self):
        summary = {}
        for order in self.orders.all():
            for item in order.order_items.all():
                name_item = summary.get(item.name_snapshot, None)
                if not name_item:
                    summary[item.name_snapshot] = {
                        "id": item.menu_item.id_checkout,
                        "quantity": item.quantity,
                        "total_cost": item.raw_cost,
                    }
                else:
                    name_item["quantity"] += item.quantity
                    name_item["total_cost"] += item.raw_cost
                # check additions
                additions = item.order_item_additions.all()
                if additions:
                    for addition in additions:
                        name_addition = summary.get(addition.name_snapshot, None)
                        if not name_addition:
                            summary[addition.name_snapshot] = {
                                "id": addition.addition.id_checkout,
                                "quantity": 1,
                                "total_cost": addition.price_snapshot,
                            }
                        else:
                            name_addition["quantity"] += 1
                            name_addition["total_cost"] += addition.price_snapshot
        return summary


class Order(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(
        max_length=20,
        choices=StatusOrder.choices,
        default=StatusOrder.ORDER,
    )
    # del ?
    table = models.ManyToManyField(Table, blank=True)
    category = models.CharField(
        default=CategoryOrder.KITCHEN, choices=CategoryOrder.choices
    )
    # Date time fields
    created_at = models.DateTimeField(auto_now_add=True)
    readied_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} - Table {self.table if self.table else 'N/A'}"

    @property
    def total(self):
        return self.order_items.aggregate(total=Sum("total_cost"))["total"]


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

    cost = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.name_snapshot} x{self.quantity}"

    @property
    def additions_cost(self):
        total = self.order_item_additions.aggregate(total=Sum("price_snapshot"))[
            "total"
        ]
        return total or Decimal("0.00")

    @property
    def total_cost(self):
        return (self.menu_item.price + self.additions_cost) * self.quantity

    @property
    def raw_cost(self):
        return self.menu_item.price * self.quantity

    @property
    def full_name_snapshot(self):
        additions = self.order_item_additions.all()
        if additions:
            additions_names = ", ".join(a.name_snapshot for a in additions)
            return f"{self.name_snapshot} ({additions_names})"
        return self.name_snapshot

    def save(self, *args, **kwargs):
        if not self.pk:
            self.cost = Decimal("0.00")
            super().save(*args, **kwargs)
        else:
            self.cost = self.total_cost
            super().save(*args, **kwargs)


class OrderItemAddition(models.Model):
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name="order_item_additions"
    )
    addition = models.ForeignKey(Addition, on_delete=models.CASCADE)
    name_snapshot = models.CharField(max_length=100)
    price_snapshot = models.DecimalField(max_digits=7, decimal_places=2)
