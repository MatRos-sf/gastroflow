from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import OrderItemAddition


@receiver(post_save, sender=OrderItemAddition)
def addition_saved(sender, instance, **kwargs):
    if instance.order_item_id:
        instance.order_item.recompute_cost(save=True)


@receiver(post_delete, sender=OrderItemAddition)
def addition_deleted(sender, instance, **kwargs):
    if instance.order_item_id:
        instance.order_item.recompute_cost(save=True)
