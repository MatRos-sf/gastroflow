from django.db.models.signals import pre_save
from django.dispatch import receiver

from order.models import Order, StatusOrder


@receiver(pre_save, sender=Order)
def update_time_field(sender, instance, **kwargs):
    if not instance.pk:
        return

    old_order = Order.objects.get(pk=instance.pk)

    if old_order.status == instance.status:
        return

    preparing_at = instance.preparing_at

    if (
        old_order.status == StatusOrder.ORDER
        and instance.status == StatusOrder.READY
        and not preparing_at
    ):
        instance.preparing_at = instance.readied_at
