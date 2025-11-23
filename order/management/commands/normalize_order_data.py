"""
Normalize OrderItemAddition quantities and clean up empty orders/bills.

This command:
- Synchronizes OrderItemAddition.quantity with parent OrderItem.quantity
- Optionally removes Orders without OrderItems
- Optionally removes Bills without Orders
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from order.models import Bill, Order, OrderItem, OrderItemAddition


class Command(BaseCommand):
    help = "Normalize OrderItemAddition quantities and remove empty orders/bills"

    def add_arguments(self, parser):
        parser.add_argument(
            "--remove-empty-orders",
            action="store_true",
            help="Remove orders that have no order items",
        )
        parser.add_argument(
            "--remove-empty-bills",
            action="store_true",
            help="Remove bills that have no orders",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without saving to database",
        )
        parser.add_argument(
            "--auto-yes",
            action="store_true",
            help="Automatically answer yes to all prompts",
        )

    def handle(self, *args, **options):
        self.dry_run = options["dry_run"]
        self.auto_yes = options["auto_yes"]
        self.remove_empty_orders = options["remove_empty_orders"]
        self.remove_empty_bills = options["remove_empty_bills"]

        # Statistics
        self.stats = {
            "additions_updated": 0,
            "orders_to_delete": [],
            "bills_to_delete": [],
        }

        if self.dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN MODE - No changes will be saved\n")
            )

        self.stdout.write("📊 Starting data normalization...\n")

        # Process all bills
        bills = Bill.objects.prefetch_related(
            "orders__order_items__order_item_additions"
        ).all()

        total_bills = bills.count()
        self.stdout.write(f"Found {total_bills} bills to process\n")

        for index, bill in enumerate(bills, start=1):
            self.stdout.write(f"\n[{index}/{total_bills}] Processing Bill #{bill.id}")
            self.process_bill(bill)

        # Show summary and confirm deletions
        self.show_summary()

        if not self.dry_run and (
            self.stats["orders_to_delete"] or self.stats["bills_to_delete"]
        ):
            self.perform_deletions()

    def process_bill(self, bill: Bill):
        """Process a single bill and its orders."""
        orders = bill.orders.all()

        if not orders:
            if self.remove_empty_bills:
                self.stdout.write(
                    self.style.WARNING("  ⚠️  Bill has no orders - marked for deletion")
                )
                self.stats["bills_to_delete"].append(
                    {
                        "id": bill.id,
                        "created": bill.created_at
                        if hasattr(bill, "created_at")
                        else "N/A",
                    }
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "  ⚠️  Bill has no orders (use --remove-empty-bills to clean)"
                    )
                )
            return

        self.stdout.write(f"  Orders: {orders.count()}")

        for order in orders:
            self.process_order(order, bill.id)

    def process_order(self, order: Order, bill_id: int):
        """Process a single order and its items."""
        order_items = order.order_items.all()

        if not order_items:
            if self.remove_empty_orders:
                self.stdout.write(
                    self.style.WARNING(
                        f"    ⚠️  Order #{order.id} has no items - marked for deletion"
                    )
                )
                self.stats["orders_to_delete"].append(
                    {
                        "id": order.id,
                        "bill_id": bill_id,
                        "created": order.created_at
                        if hasattr(order, "created_at")
                        else "N/A",
                    }
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"    ⚠️  Order #{order.id} has no items (use --remove-empty-orders to clean)"
                    )
                )
            return

        for order_item in order_items:
            self.process_order_item(order_item, order.id, bill_id)

    def process_order_item(self, order_item: OrderItem, order_id: int, bill_id: int):
        """Process a single order item and sync its additions."""
        additions = order_item.order_item_additions.all()

        if not additions:
            return

        mismatched = []
        for addition in additions:
            if addition.quantity != order_item.quantity:
                mismatched.append(addition)

        if not mismatched:
            return

        # Show details about mismatches
        self.stdout.write(
            f"    📦 OrderItem #{order_item.id} "
            f"(Bill #{bill_id}, Order #{order_id}, qty: {order_item.quantity})"
        )

        for addition in mismatched:
            self.stdout.write(
                f"      ⚠️  Addition #{addition.id}: "
                f"quantity {addition.quantity} → {order_item.quantity}"
            )

            # Ask for confirmation if not auto-yes
            if not self.auto_yes and not self.dry_run:
                response = self.ask_user_confirmation(
                    "        Update this addition? (y/n/a=yes to all): ",
                    valid_responses=["y", "n", "a"],
                )

                if response == "a":
                    self.auto_yes = True
                    self.update_addition(addition, order_item.quantity)
                elif response == "y":
                    self.update_addition(addition, order_item.quantity)
                else:
                    self.stdout.write(self.style.WARNING("        Skipped"))
            else:
                self.update_addition(addition, order_item.quantity)

    def update_addition(self, addition: OrderItemAddition, new_quantity: int):
        """Update addition quantity."""
        if not self.dry_run:
            addition.quantity = new_quantity
            addition.save(update_fields=["quantity"])
            self.stdout.write(self.style.SUCCESS("        ✓ Updated"))
        else:
            self.stdout.write(self.style.SUCCESS("        ✓ Would update (dry-run)"))

        self.stats["additions_updated"] += 1

    def ask_user_confirmation(self, message: str, valid_responses: list) -> str:
        """Ask user for confirmation."""
        while True:
            response = input(message).lower().strip()
            if response in valid_responses:
                return response
            self.stdout.write(
                self.style.ERROR(
                    f'Invalid response. Expected one of: {", ".join(valid_responses)}'
                )
            )

    def show_summary(self):
        """Display summary of changes."""
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("📊 SUMMARY"))
        self.stdout.write("=" * 70)

        self.stdout.write(f'Additions updated: {self.stats["additions_updated"]}')

        if self.stats["orders_to_delete"]:
            self.stdout.write(
                self.style.WARNING(
                    f'\nOrders marked for deletion: {len(self.stats["orders_to_delete"])}'
                )
            )
            for order_info in self.stats["orders_to_delete"][:5]:
                self.stdout.write(
                    f'  • Order #{order_info["id"]} (Bill #{order_info["bill_id"]})'
                )
            if len(self.stats["orders_to_delete"]) > 5:
                self.stdout.write(
                    f'  ... and {len(self.stats["orders_to_delete"]) - 5} more'
                )

        if self.stats["bills_to_delete"]:
            self.stdout.write(
                self.style.WARNING(
                    f'\nBills marked for deletion: {len(self.stats["bills_to_delete"])}'
                )
            )
            for bill_info in self.stats["bills_to_delete"][:5]:
                self.stdout.write(f'  • Bill #{bill_info["id"]}')
            if len(self.stats["bills_to_delete"]) > 5:
                self.stdout.write(
                    f'  ... and {len(self.stats["bills_to_delete"]) - 5} more'
                )

        self.stdout.write("=" * 70)

    def perform_deletions(self):
        """Execute deletions after user confirmation."""
        total_deletions = len(self.stats["orders_to_delete"]) + len(
            self.stats["bills_to_delete"]
        )

        if total_deletions == 0:
            return

        self.stdout.write(f"\n⚠️  About to delete {total_deletions} records")

        if not self.auto_yes:
            response = self.ask_user_confirmation(
                "Are you sure you want to proceed? (yes/no): ", ["yes", "no"]
            )
            if response != "yes":
                self.stdout.write(self.style.WARNING("Deletion cancelled"))
                return

        with transaction.atomic():
            # Delete orders first
            if self.stats["orders_to_delete"]:
                order_ids = [o["id"] for o in self.stats["orders_to_delete"]]
                deleted_orders = Order.objects.filter(id__in=order_ids).delete()
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Deleted {deleted_orders[0]} orders")
                )

            # Then delete bills
            if self.stats["bills_to_delete"]:
                bill_ids = [b["id"] for b in self.stats["bills_to_delete"]]
                deleted_bills = Bill.objects.filter(id__in=bill_ids).delete()
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Deleted {deleted_bills[0]} bills")
                )

        self.stdout.write(self.style.SUCCESS("\n✅ Cleanup completed successfully"))
