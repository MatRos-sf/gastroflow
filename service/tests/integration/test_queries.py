from django.test import TestCase
from model_bakery import baker

from order.models import Bill, StatusBill
from service.models import Table
from service.queries import release_tables


class TestReleaseTables(TestCase):
    def setUp(self):
        self.table = baker.make(Table, is_occupied=True)

    def _make_bill(self, status: StatusBill, table: Table | None = None) -> Bill:
        bill = baker.make(Bill, status=status)
        bill.table.set([table or self.table])
        return bill

    def test_releases_table_when_no_other_open_bills(self):
        """Table should be freed after the only bill is closed."""
        bill = self._make_bill(StatusBill.CLOSED)

        release_tables(bill)

        self.table.refresh_from_db()
        self.assertFalse(self.table.is_occupied)

    def test_does_not_release_table_when_another_open_bill_exists(self):
        """Table should stay occupied when another OPEN bill shares it."""
        closed_bill = self._make_bill(StatusBill.CLOSED)
        self._make_bill(StatusBill.OPEN)

        release_tables(closed_bill)

        self.table.refresh_from_db()
        self.assertTrue(self.table.is_occupied)

    def test_does_not_release_table_when_closed_and_occupied_bill_exists(self):
        """Table should stay occupied when a CLOSED_AND_OCCUPIED bill shares it."""
        closed_bill = self._make_bill(StatusBill.CLOSED)
        self._make_bill(StatusBill.CLOSED_AND_OCCUPIED)

        release_tables(closed_bill)

        self.table.refresh_from_db()
        self.assertTrue(self.table.is_occupied)

    def test_does_not_release_table_for_bill_without_tables(self):
        """Calling release_tables on a bill with no tables should not crash."""
        bill = baker.make(Bill, status=StatusBill.CLOSED)

        release_tables(bill)

        self.table.refresh_from_db()
        self.assertTrue(self.table.is_occupied)

    def test_releases_only_tables_with_no_remaining_open_bills(self):
        """When a bill spans two tables, only the table with no other open bills is released."""
        table_free = baker.make(Table, is_occupied=True)
        table_busy = baker.make(Table, is_occupied=True)

        closed_bill = baker.make(Bill, status=StatusBill.CLOSED)
        closed_bill.table.set([table_free, table_busy])

        self._make_bill(StatusBill.OPEN, table=table_busy)

        release_tables(closed_bill)

        table_free.refresh_from_db()
        table_busy.refresh_from_db()
        self.assertFalse(table_free.is_occupied)
        self.assertTrue(table_busy.is_occupied)
