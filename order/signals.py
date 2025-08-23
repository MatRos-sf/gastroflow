# order/signals.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from order.models import Notification, NotificationStatus, Order, StatusOrder


@receiver(pre_save, sender=Order)
def order_pre_save(sender, instance: Order, **kwargs):
    if instance.pk:
        # bezpiecznie pobieramy wcześniejszy status i podpinamy do instancji
        instance._prev_status = (
            Order.objects.filter(pk=instance.pk)
            .values_list("status", flat=True)
            .first()
        )
    else:
        instance._prev_status = None

    # (twój dotychczasowy kod z przygotowaniem preparing_at)
    if instance.pk:
        old_status = instance._prev_status
        if (
            old_status == StatusOrder.ORDER
            and instance.status == StatusOrder.READY
            and not instance.preparing_at
        ):
            # jeśli ktoś przeskoczył PREPARING, ustaw preparing_at = readied_at
            # (uwaga: readied_at ustawisz później)
            instance.preparing_at = instance.readied_at


@receiver(post_save, sender=Order)
def order_post_save(sender, instance: Order, created, **kwargs):
    if created:
        return

    prev = getattr(instance, "_prev_status", None)
    if prev != StatusOrder.READY and instance.status == StatusOrder.READY:
        # Wykonaj po commicie, żeby stan w DB był już stabilny
        def _after_commit():
            qs = Notification.objects.select_related(
                "worker", "order_item", "order_item__order", "order_item__order__bill"
            ).filter(
                order_item__order=instance,
                status=NotificationStatus.PREPARE,
            )

            now = timezone.now()
            payloads = [
                {
                    "id": n.id,
                    "worker": str(n.worker),
                    "order_item": n.order_item.full_name_snapshot
                    + (f" ({n.order_item.note})" if n.order_item.note else ""),
                    "table": n.order_item.order.bill.str_tables(),
                    "last_update": now.isoformat(),
                    "status": NotificationStatus.WAIT,
                }
                for n in qs
            ]

            qs.update(status=NotificationStatus.WAIT, last_update=now)

            if payloads:
                cl = get_channel_layer()
                for p in payloads:
                    async_to_sync(cl.group_send)(
                        "notifications", {"type": "new_notification", **p}
                    )

        transaction.on_commit(_after_commit)
