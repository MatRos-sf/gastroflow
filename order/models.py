from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from menu.models import Item, Location
from service.models import Table
from worker.models import Worker


class OrderItemStatus(models.TextChoices):
    WAITING = "waiting", "WAITING"
    PREPARING = "preparing", "PREPARING"
    READY = "ready", "READY"
    CANCELED = "canceled", "CANCELED"


class StatusOrder(models.TextChoices):
    ORDER = "ordering", "ORDERING"
    PREPARING = "preparing", "PREPARING"
    READY = "ready", "READY"
    PAID = "paid", "PAID"
    CANCELED = "canceled", "CANCELED"


class StatusBill(models.TextChoices):
    OPEN = "open", "OPEN"
    CLOSED = "closed", "CLOSED"


class PaymentMethod(models.TextChoices):
    CARD = "card", "Karta"
    CASH = "cash", "Gotówka"


class Bill(models.Model):
    table = models.ManyToManyField(Table, blank=True)
    status = models.CharField(
        max_length=10, choices=StatusBill.choices, default=StatusBill.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    service = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Person who served the customer",
    )
    note = models.CharField(max_length=200, blank=True, null=True)
    discount = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    payment_method = models.CharField(
        max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CARD
    )

    # Payment additional
    # is_cash
    # tip
    # given_money
    def __str__(self):
        return f"Bill {self.id} - Table {self.table or 'take-away'}"

    def str_tables(self):
        return ", ".join(str(table.name) for table in self.table.all())

    @property
    def total(self):
        s = self.bill_summary_view()
        return s["total"] - s["cost_discount"]

    def close(self):
        self.status = StatusBill.CLOSED
        self.closed_at = timezone.now()
        self.save()

    def bill_summary_view(self):
        summary = {}
        total = Decimal("0.00")

        orders = self.orders.prefetch_related("order_items__order_item_additions")
        for order in orders:
            for item in order.order_items.all():
                # main dish
                summary.setdefault(
                    item.name_snapshot,
                    {
                        "id": item.menu_item.id_checkout,
                        "quantity": 0,
                        "total_cost": Decimal("0.00"),
                    },
                )
                summary[item.name_snapshot]["quantity"] += item.quantity
                summary[item.name_snapshot]["total_cost"] += item.raw_cost

                total += item.raw_cost

                # check additions
                for addition in item.order_item_additions.all():
                    summary.setdefault(
                        addition.name_snapshot,
                        {
                            "id": addition.addition.id_checkout,
                            "quantity": 0,
                            "total_cost": Decimal("0.00"),
                        },
                    )
                    summary[addition.name_snapshot]["quantity"] += item.quantity
                    summary[addition.name_snapshot]["total_cost"] += (
                        addition.price_snapshot * item.quantity
                    )
                    total += addition.price_snapshot * item.quantity
        cost_discount = (total * self.discount) / 100

        return {"total": total, "summary": summary, "cost_discount": cost_discount}


class Order(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(
        max_length=20,
        choices=StatusOrder.choices,
        default=StatusOrder.ORDER,
    )
    category = models.CharField(default=Location.KITCHEN, choices=Location.choices)
    # Date time fields
    created_at = models.DateTimeField(auto_now_add=True)
    preparing_at = models.DateTimeField(null=True, blank=True)
    readied_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.id}"

    # @property
    # def total(self):
    #     return self.order_items.aggregate(total=Sum("total_cost"))["total"]
    def total(self):
        return (
            self.order_items.annotate(
                additions_total=Coalesce(Sum("order_item_additions__price_snapshot"), 0)
            )
            .annotate(
                line=ExpressionWrapper(
                    F("price_snapshot") * F("quantity") + F("additions_total"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
            .aggregate(total=Coalesce(Sum("line"), 0))["total"]
        )


class NotificationStatus(models.TextChoices):
    PREPARE = "prepare", "Prepare"  # when kitchen is preparing the order
    WAIT = "wait", "Wait"  # when the dish waiting to be served
    SERVE = "serve", "Serve"  # when the dish is served


class Notification(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    order_item = models.OneToOneField("order.OrderItem", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PREPARE,
    )
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"@{self.worker} - {self.order_item.name_snapshot} | {self.order_item.order.bill.str_tables()}"


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
    status = models.CharField(
        max_length=20, choices=OrderItemStatus.choices, default=OrderItemStatus.WAITING
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Datetime order was added"
    )
    started_at = models.DateTimeField(
        null=True, blank=True, help_text="Datetime when the cook started preparing"
    )
    finished_at = models.DateTimeField(
        null=True, blank=True, help_text="Datetime when the cook finished preparing"
    )
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.name_snapshot} x{self.quantity}"

    @property
    def raw_cost(self):
        """Cost without additions"""
        return self.price_snapshot * self.quantity

    @property
    def total_cost(self):
        """Cost with additions"""
        additions = self.order_item_additions.aggregate(
            additions_sum=Coalesce(Sum("price_snapshot"), 0)
        )["additions_sum"]
        return (self.price_snapshot + additions) * self.quantity

    @property
    def full_name_snapshot(self):
        additions = self.order_item_additions.all()
        if additions.exists():
            additions_names = ", ".join(a.name_snapshot for a in additions)
            return f"{self.name_snapshot} ({additions_names})"
        return self.name_snapshot

    def save(self, *args, **kwargs):
        is_init = self.pk is None

        super().save(*args, **kwargs)

        # create notification only for new order items
        if is_init:
            service_worker = getattr(self.order.bill, "service", None)
            if service_worker is not None:
                Notification.objects.create(worker=service_worker, order_item=self)


class OrderItemAddition(models.Model):
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name="order_item_additions"
    )
    addition = models.ForeignKey(Item, on_delete=models.CASCADE)
    name_snapshot = models.CharField(max_length=100)
    price_snapshot = models.DecimalField(max_digits=7, decimal_places=2)
