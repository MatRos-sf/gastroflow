from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone

from menu.models import Addition, Item, Location
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
    table = models.ManyToManyField(
        Table,
        blank=True,
        null=True,
        help_text="Table to which the bill is assigned. Null means take-away",
    )
    status = models.CharField(
        max_length=10, choices=StatusBill.choices, default=StatusBill.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(
        null=True, blank=True
    )  # Customer can pay but occupied table
    closed_at = models.DateTimeField(
        null=True, blank=True
    )  # When customer leave restaurant
    waiter = models.ForeignKey(
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

    guest_count = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of people in one the bill (plates per person)",
    )

    def __str__(self):
        return f"Bill {self.id} - Table {self.table or 'take-away'}"

    def get_absolute_url(self):
        return reverse("bill-detail", args=[str(self.id)])

    # TODO: deprecated ?
    def str_tables(self):
        return ", ".join(str(table.name) for table in self.table.all())

    # TODO: deprecated ?
    @property
    def total(self):
        s = self.bill_summary_view()
        return s["total"] - s["cost_discount"]

    # TODO: deprecated ?
    def close(self):
        self.status = StatusBill.CLOSED
        self.closed_at = timezone.now()
        self.save()

    # #TODO: deprecated ?
    # def _distribute_discount_proportionally(
    #     self, model_class, discount_amount: Decimal, total_bill_amount: Decimal
    # ) -> None:
    #     """
    #     Distribute discount proportionally across items based on their subtotal.
    #
    #     The discount for each item is calculated as:
    #     item_discount = (item_subtotal / total_bill_amount) * total_discount_amount
    #
    #     Args:
    #         model_class: Model to update (OrderItem or OrderItemAddition)
    #         discount_amount: Total discount amount to distribute (in currency)
    #         total_bill_amount: Sum of all line_subtotals (order items + additions)
    #
    #     Example:
    #         If bill total is 100 PLN with 10% discount (10 PLN):
    #         - Item with subtotal 50 PLN gets: (50/100) * 10 = 5 PLN discount
    #         - Item with subtotal 30 PLN gets: (30/100) * 10 = 3 PLN discount
    #     """
    #     if not total_bill_amount or total_bill_amount == 0:
    #         return
    #
    #     # Determine filter based on model type
    #     if model_class == OrderItem:
    #         filter_kwargs = {"order__bill": self}
    #     elif model_class == OrderItemAddition:
    #         filter_kwargs = {"order_item__order__bill": self}
    #     else:
    #         raise ValueError(
    #             "Invalid model item: should be OrderItem or OrderItemAddition"
    #         )
    #
    #     items = list(model_class.objects.filter(**filter_kwargs))
    #
    #     for item in items:
    #         proportion = item.line_subtotal / total_bill_amount
    #         item.line_discount_amount = proportion * discount_amount
    #
    #     # Bulk update for performance
    #     if items:
    #         model_class.objects.bulk_update(items, ["line_discount_amount"])

    # #TODO: deprecated ?
    # def add_discount(self, discount_percentage: int) -> None:
    #     """
    #     Apply a percentage discount to the bill and distribute it across all items.
    #
    #     The discount is distributed proportionally based on each item's subtotal.
    #     Updates line_discount_amount for all OrderItems and OrderItemAdditions.
    #     Args:
    #         discount_percentage: Discount percentage to apply (0-100)
    #
    #     Raises:
    #         ValidationError: If discount_percentage is not between 0 and 100
    #
    #     Example:
    #         bill.add_discount(10)  # Apply 10% discount to entire bill
    #     """
    #     if not 0 <= discount_percentage <= 100:
    #         raise ValidationError("Discount must be between 0 and 100")
    #
    #     self.discount = discount_percentage
    #     self.save(update_fields=["discount"])
    #
    #     order_items_total = (
    #         OrderItem.objects.filter(order__bill=self).aggregate(
    #             order_items=Sum("line_subtotal")
    #         )["order_items"]
    #         or 0
    #     )
    #     additions_total = (
    #         OrderItemAddition.objects.filter(order_item__order__bill=self).aggregate(
    #             additions=Sum("line_subtotal")
    #         )["additions"]
    #         or 0
    #     )
    #
    #     bill_total = Decimal(order_items_total + additions_total)
    #     if bill_total == 0:
    #         return  # Nothing to discount
    #     discount_amount = Decimal(bill_total * discount_percentage / 100)
    #
    #     # Distribute discount proportionally to all items
    #     self._distribute_discount_proportionally(OrderItem, discount_amount, bill_total)
    #     self._distribute_discount_proportionally(
    #         OrderItemAddition, discount_amount, bill_total
    #     )

    # #TODO: deprecated ?
    # def bill_summary_view(self):
    #     summary = {}
    #     total = Decimal("0.00")
    #
    #     orders = self.orders.prefetch_related("order_items__order_item_additions")
    #     for order in orders:
    #         for item in order.order_items.all():
    #             # main dish
    #             summary.setdefault(
    #                 item.name_snapshot,
    #                 {
    #                     "id": item.menu_item.id_checkout,
    #                     "quantity": 0,
    #                     "total_cost": Decimal("0.00"),
    #                 },
    #             )
    #             summary[item.name_snapshot]["quantity"] += item.quantity
    #             summary[item.name_snapshot]["total_cost"] += item.raw_cost
    #
    #             total += item.raw_cost
    #
    #             # check additions
    #             for addition in item.order_item_additions.all():
    #                 summary.setdefault(
    #                     addition.name_snapshot,
    #                     {
    #                         "id": addition.addition.id_checkout,
    #                         "quantity": 0,
    #                         "total_cost": Decimal("0.00"),
    #                     },
    #                 )
    #                 summary[addition.name_snapshot]["quantity"] += item.quantity
    #                 summary[addition.name_snapshot]["total_cost"] += (
    #                     addition.price_snapshot * item.quantity
    #                 )
    #                 total += addition.price_snapshot * item.quantity
    #     cost_discount = (total * self.discount) / 100
    #
    #     return {"total": total, "summary": summary, "cost_discount": cost_discount}


class NotificationType(models.TextChoices):
    ITEM_INFO = "item_info", "Item Info"
    ORDER_INFO = "order_info", "Order Info"
    CALL = "call", "Call"


class NotificationStatus(models.TextChoices):
    NONE = "none", "None"
    WAITING_TO_READ = "waiting_to_read", "Waiting to Read"
    READ = "read", "Read"


class Notification(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    notification_type = models.CharField(
        max_length=20, choices=NotificationType.choices
    )
    item = models.ForeignKey(
        "order.OrderItem", on_delete=models.CASCADE, null=True, blank=True
    )
    order = models.ForeignKey(
        "order.Order", on_delete=models.CASCADE, null=True, blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.NONE,
    )
    message = models.CharField(max_length=400, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    @property
    def tables(self) -> str:
        if not self.order and self.item:
            return ""
        if self.order:
            return "Tables form set order #TODO"

        return "Tables form set item #TODO"


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
    canceled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.id}"

    def save(self, *args, **kwargs):
        is_init = self.pk is None
        super().save(*args, **kwargs)
        if is_init:
            create_notification(
                worker=self.bill.waiter,
                notification_type=NotificationType.ORDER_INFO,
                order=self,
            )

    # TODO: deprecated ?
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


class OrderBase(models.Model):
    name_snapshot = models.CharField(
        max_length=150, help_text="Name of dish or additions"
    )
    price_snapshot = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Price of dish or additions when it was ordered",
    )
    quantity = models.PositiveIntegerField(default=1)
    line_subtotal = models.GeneratedField(
        expression=F("price_snapshot") * F("quantity"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
        help_text="Subtotal for this item before discount and additions (price × quantity)",
        db_persist=True,
    )

    class Meta:
        abstract = True


class OrderItem(OrderBase):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items"
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    note = models.TextField(null=True, blank=True, max_length=500)
    status = models.CharField(
        max_length=20, choices=OrderItemStatus.choices, default=OrderItemStatus.WAITING
    )
    # # TODO: write function than set this field!
    # line_discount_amount = models.DecimalField(
    #     default=Decimal("0.00"),
    #     max_digits=12,
    #     decimal_places=2,
    #     help_text="Discount amount allocated from bill's discount percentage. You should change it manually!",
    # )
    # line_final_total = models.GeneratedField(
    #     expression=F("line_subtotal") - F("line_discount_amount"),
    #     output_field=DecimalField(max_digits=12, decimal_places=2),
    #     db_persist=True,
    #     help_text="Final price for this addition after discount",
    # )

    def __str__(self):
        return f"{self.name_snapshot} x{self.quantity}"

    # TODO: deprecated?
    @property
    def raw_cost(self):
        """Cost without additions"""
        return self.price_snapshot * self.quantity

    # #TODO: deprecated?
    # @property
    # def total_cost(self):
    #     """Cost with additions"""
    #     additions = self.order_item_additions.aggregate(
    #         additions_sum=Coalesce(Sum("price_snapshot"), 0)
    #     )["additions_sum"]
    #     return (self.price_snapshot + additions) * self.quantity

    # #TODO: deprecated?
    # @property
    # def full_name_snapshot(self):
    #     additions = self.order_item_additions.all()
    #     if additions.exists():
    #         additions_names = ", ".join(a.name_snapshot for a in additions)
    #         return f"{self.name_snapshot} ({additions_names})"
    #     return self.name_snapshot

    def save(self, *args, **kwargs):
        is_init = self.pk is None
        super().save(*args, **kwargs)

        if is_init:
            create_notification(
                worker=self.order.bill.waiter,
                notification_type=NotificationType.ITEM_INFO,
                item=self,
            )


class OrderItemAddition(OrderBase):
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name="order_item_additions"
    )
    addition = models.ForeignKey(Addition, on_delete=models.CASCADE)

    # line_discount_amount = models.DecimalField(
    #     default=Decimal("0.00"),
    #     max_digits=12,
    #     decimal_places=2,
    #     help_text="The amount of discount from Bill. You should change it manually!",
    # )
    # line_final_total = models.GeneratedField(
    #     expression=F("line_subtotal") - F("line_discount_amount"),
    #     output_field=DecimalField(max_digits=12, decimal_places=2),
    #     db_persist=True,
    #     help_text="Final price for this addition after discount",
    # )


def create_notification(
    worker: Worker,
    notification_type: NotificationType,
    message: str | None = None,
    order: Order | None = None,
    item: OrderItem | None = None,
    status: NotificationStatus = NotificationStatus.NONE,
):
    if order and item:
        raise ValueError("Order and item cannot be both set")

    return Notification.objects.create(
        worker=worker,
        notification_type=notification_type,
        item=item,
        order=order,
        status=status,
        message=message,
    )
