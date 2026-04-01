from order.models import Bill, StatusBill


def release_tables(bill: Bill) -> None:
    for table in bill.table.all():
        if not Bill.objects.filter(
            table=table, status__in=[StatusBill.OPEN, StatusBill.CLOSED_AND_OCCUPIED]
        ).exists():
            table.is_occupied = False
            table.save(update_fields=["is_occupied"])
