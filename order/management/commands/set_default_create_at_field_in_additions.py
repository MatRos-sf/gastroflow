from django.core.management.base import BaseCommand
from django.db import transaction

from order.models import OrderItemAddition


class Command(BaseCommand):
    help = "Update additions created_at field according to related order_item"

    def handle(self, *args, **options):
        additions = OrderItemAddition.objects.select_related("order_item").all()
        self.stdout.write("Updating additions created_at field")
        for addition in additions:
            with transaction.atomic():
                addition.created_at = addition.order_item.created_at
                addition.save(update_fields=["created_at"])
                self.stdout.write(".", ending="")

        self.stdout.write("\nUpdating additions has been done!\n")
