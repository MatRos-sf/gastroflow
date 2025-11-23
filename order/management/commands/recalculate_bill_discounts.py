from django.core.management.base import BaseCommand
from django.db import transaction

from order.models import Bill


class Command(BaseCommand):
    help = "Recalculate discount distribution for all bills (line_subtotal, line_discount_amount, line_final_total)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run without actually saving changes to database",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if dry_run:
            self.stdout.write(
                self.style.WARNING("Running in DRY RUN mode - no changes will be saved")
            )

        bills = Bill.objects.all()
        total_bills = bills.count()

        if not total_bills:
            self.stdout.write(self.style.WARNING("No bills found in database"))
            return

        self.stdout.write(
            self.style.SUCCESS(f"Found {total_bills} bills to update ..\n")
        )

        success_count = 0
        error_count = 0

        for index, bill in enumerate(bills, start=1):
            try:
                discount = bill.discount
                bill_id = bill.id
                self.stdout.write(
                    f"[{index}/{total_bills}] Updating Bill ID: {bill_id} (discount: {discount}%)... ",
                    ending="",
                )
                self.stdout.write(f"{dry_run = }")

                with transaction.atomic():
                    self.stdout.write("I'm here!")
                    bill.add_discount(discount)

                self.stdout.write(self.style.SUCCESS("✓"))
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error: {str(e)}"))
                error_count += 1

        self.stdout.write("\n" + "=" * 50)
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN COMPLETED"))
        else:
            self.stdout.write(self.style.SUCCESS("UPDATE COMPLETED"))

        self.stdout.write(f"Total bills: {total_bills}")
        self.stdout.write(self.style.SUCCESS(f"Successfully updated: {success_count}"))

        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"Errors: {error_count}"))

        self.stdout.write("=" * 50)
