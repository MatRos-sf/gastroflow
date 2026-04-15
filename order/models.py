from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from menu.models import Addition, Item, Location
from service.models import Table
from worker.models import Worker


class OrderItemStatus(models.TextChoices):
    WAITING = "waiting", _("Waiting")
    PREPARING = "preparing", _("Preparing")
    READY = "ready", _("Ready")
    CANCELED = "canceled", _("Canceled")


class StatusOrder(models.TextChoices):
    ORDER = "ordering", _("Ordering")
    PREPARING = "preparing", _("Preparing")
    READY = "ready", _("Ready")
    PAID = "paid", _("Paid")
    CANCELED = "canceled", _("Canceled")


class StatusBill(models.TextChoices):
    """
    Bill status lifecycle:
        * OPEN: bill active, table occupied, not paid
        * CLOSED: bill paid, table unoccupied
        * CLOSED_AND_OCCUPIED: bill paid, table still occupied
    """

    OPEN = "open", _("Open")
    CLOSED = "closed", _("Closed")
    CLOSED_AND_OCCUPIED = "closed_and_occupied", _("Closed and occupied")


class PaymentMethod(models.TextChoices):
    CARD = "card", _("Card")
    CASH = "cash", _("Cash")
    CASH_AND_CARD = "cash_and_card", _("Cash and card")


class Bill(models.Model):
    table = models.ManyToManyField(
        Table,
        help_text=_("Table to which the bill is assigned. Null means take-away"),
    )
    status = models.CharField(
        max_length=19, choices=StatusBill.choices, default=StatusBill.OPEN
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
        help_text=_("Person who served the customer"),
    )
    note = models.CharField(max_length=200, blank=True, null=True)
    discount = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    payment_method = models.CharField(
        max_length=13, choices=PaymentMethod.choices, default=None, null=True
    )
    guest_count = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_("Number of people in one the bill (plates per person)"),
    )
    is_printed = models.BooleanField(default=False)
    printed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Bill {self.id} - Table {self.table or 'take-away'}"

    def get_absolute_url(self):
        return reverse("detail-bill", args=[str(self.id)])

    @property
    def is_open(self) -> bool:
        return self.status == StatusBill.OPEN

    @property
    def is_closed(self) -> bool:
        return self.status == StatusBill.CLOSED

    @property
    def is_closed_and_occupied(self) -> bool:
        return self.status == StatusBill.CLOSED_AND_OCCUPIED

    # TODO: deprecated ?
    def str_tables(self) -> str:
        return ", ".join(
            f"{table.hall.name} · {table.name}"
            for table in self.table.select_related("hall").all()
        )

    # TODO: deprecated ?
    def close(self):
        self.status = StatusBill.CLOSED
        self.closed_at = timezone.now()
        self.save()

    @property
    def compute_total(self):
        total = Decimal("0.00")
        for order in self.orders.all():
            for item in order.order_items.all():
                total += item.line_subtotal
                for additions in item.order_item_additions.all():
                    total += additions.line_subtotal
        return total


class BillReceipt(models.Model):
    bill = models.OneToOneField(Bill, on_delete=models.CASCADE, related_name="receipt")
    ok = models.BooleanField()
    hn = models.CharField(max_length=20, help_text=_("Unique fiscal receipt number"))
    bn = models.CharField(max_length=20, help_text=_("Session receipt number"))
    took = models.PositiveIntegerField(help_text=_("Print time in ms"))
    raw_response = models.JSONField(help_text=_("Full POSNET response"))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Receipt hn={self.hn} for Bill {self.bill.pk}"


class NotificationType(models.TextChoices):
    ITEM_INFO = "item_info", _("Item Info")
    ORDER_INFO = "order_info", _("Order Info")
    CALL = "call", _("Call")


class NotificationStatus(models.TextChoices):
    NONE = "none", _("None")
    WAITING_TO_READ = "waiting_to_read", _("Waiting to Read")
    READ = "read", _("Read")


class Notification(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    notification_type = models.CharField(
        max_length=20, choices=NotificationType.choices
    )
    item = models.OneToOneField(
        "order.OrderItem", on_delete=models.CASCADE, null=True, blank=True
    )
    order = models.OneToOneField(
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
    def tables(self) -> str | None:
        if not self.order and self.item:
            qs = self.item.order.bill.tables.all()
            return ",".join(table.name for table in qs)
        if self.order:
            qs = self.order.bill.tables.all()
            return ",".join(table.name for table in qs)

        return None


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
        max_length=150, help_text=_("Name of dish or additions")
    )
    price_snapshot = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text=_("Price of dish or additions when it was ordered"),
    )
    quantity = models.PositiveIntegerField(default=1)
    line_subtotal = models.GeneratedField(
        expression=F("price_snapshot") * F("quantity"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
        help_text=_(
            "Subtotal for this item before discount and additions (price × quantity)"
        ),
        db_persist=True,
    )
    line_final_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Final price after bill discount. Set when  bill is closed.",
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

    def __str__(self):
        return f"{self.name_snapshot} x{self.quantity}"

    @property
    def additions_str(self):
        return ", ".join(
            addition.name_snapshot for addition in self.order_item_additions.all()
        )

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
