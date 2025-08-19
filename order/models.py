from decimal import Decimal, InvalidOperation

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F, Sum, Value
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
        raise NotImplementedError

    def close(self):
        self.status = StatusBill.CLOSED
        self.closed_at = timezone.now()
        self.save()

    def bill_summary_view(self):
        summary = {}
        total = Decimal("0.00")
        for order in self.orders.all():
            for item in order.order_items.all():
                name_item = summary.get(item.name_snapshot, None)
                cost = item.raw_cost
                if not name_item:
                    summary[item.name_snapshot] = {
                        "id": item.menu_item.id_checkout,
                        "quantity": item.quantity,
                        "total_cost": cost,
                    }
                else:
                    name_item["quantity"] += item.quantity
                    name_item["total_cost"] += cost
                total += cost
                # check additions
                additions = item.order_item_additions.all()
                if additions:
                    for addition in additions:
                        name_addition = summary.get(addition.name_snapshot, None)
                        cost = addition.price_snapshot
                        if not name_addition:
                            summary[addition.name_snapshot] = {
                                "id": addition.addition.id_checkout,
                                "quantity": 1,
                                "total_cost": cost,
                            }
                        else:
                            name_addition["quantity"] += 1
                            name_addition["total_cost"] += cost
                        total += cost
        return {"total": total, "summary": summary}


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
        additions = self.order_item_additions.aggregate(
            total=Coalesce(Sum("price_snapshot"), 0)
        )["total"]
        return (self.price_snapshot + additions) * self.quantity

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

    @staticmethod
    def _to_decimal(val, default="0.00") -> Decimal:
        """Bezpieczna konwersja na Decimal niezależnie czy wejdzie str/int/None."""
        if isinstance(val, Decimal):
            return val
        if val is None:
            return Decimal(default)
        try:
            # str() chroni np. przed typem int/float; waluty z przecinkiem trzeba oczyścić wcześniej.
            return Decimal(str(val))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal(default)

    def recompute_cost(self, save=True):
        # Zwracaj 0 jako Decimal, a nie int/str
        zero = Value(
            Decimal("0.00"),
            output_field=models.DecimalField(max_digits=12, decimal_places=2),
        )

        additions_total = self.order_item_additions.aggregate(
            total=Coalesce(Sum("price_snapshot"), zero)
        )["total"]

        price = self._to_decimal(self.price_snapshot)
        adds = self._to_decimal(additions_total)
        qty = self._to_decimal(self.quantity)

        new_cost = (price + adds) * qty
        self.cost = new_cost

        if save and self.pk:
            # update -> nie wywołujemy z powrotem save()
            OrderItem.objects.filter(pk=self.pk).update(cost=new_cost)

    def save(self, *args, **kwargs):
        is_init = self.pk is None

        # 1) Zapisz najpierw, żeby mieć PK (reverse relacje potrzebują PK)
        super().save(*args, **kwargs)

        # 2) Przelicz koszt już po tym, jak obiekt istnieje w DB
        self.recompute_cost(save=True)

        # 3) Notification tylko przy utworzeniu i tylko jeśli jest przypisany worker
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
