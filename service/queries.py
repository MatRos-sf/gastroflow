from django.utils import timezone

from order.models import Bill, StatusBill
from service.models import Table


def _release_table(table: Table) -> None:
    table.is_occupied = False
    table.save(update_fields=["is_occupied"])


def release_tables(bill: Bill) -> None:
    for table in bill.table.all():
        if not Bill.objects.filter(
            table=table, status__in=[StatusBill.OPEN, StatusBill.CLOSED_AND_OCCUPIED]
        ).exists():
            _release_table(table)


def release_tables_for_open_bill(bill: Bill) -> None:
    for table in bill.table.all():
        if (
            not Bill.objects.filter(
                table=table,
                status__in=[StatusBill.OPEN, StatusBill.CLOSED_AND_OCCUPIED],
            )
            .exclude(pk=bill.pk)
            .exists()
        ):
            _release_table(table)


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
