from django.utils import timezone

from order.models import Bill, StatusBill


def release_tables(bill: Bill) -> None:
    for table in bill.table.all():
        if not Bill.objects.filter(
            table=table, status__in=[StatusBill.OPEN, StatusBill.CLOSED_AND_OCCUPIED]
        ).exists():
            table.is_occupied = False
            table.save(update_fields=["is_occupied"])


def process_bill_closure(
    bill: Bill,
    status: str,
    payment_method: str | None = None,
) -> None:
    bill.status = status
    bill.closed_at = timezone.now()
    update_fields = ["status", "closed_at"]
    if payment_method:
        bill.payment_method = payment_method
        update_fields.append("payment_method")

    bill.save(update_fields=update_fields)
