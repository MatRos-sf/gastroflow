from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from order.models import StatusBill
from order.raport import CountBillStatus


class TestCountBillStatus(TestCase):
    FIRST_DAY_CREATED_AT = timezone.make_aware(datetime(2022, 1, 1))
    SECOND_DAY_CREATED_AT = timezone.make_aware(datetime(2022, 1, 2))
    OPEN_BILLS = 5
    CLOSED_BILLS_FIRST_DAY = 3
    CLOSED_BILLS_SECOND_DAY = 3

    def setUp(self):
        for _ in range(self.OPEN_BILLS):
            baker.make(
                "order.Bill",
                created_at=self.FIRST_DAY_CREATED_AT,
                status=StatusBill.OPEN,
            )
        for _ in range(self.CLOSED_BILLS_FIRST_DAY):
            baker.make(
                "order.Bill",
                created_at=self.FIRST_DAY_CREATED_AT,
                status=StatusBill.CLOSED,
            )
        for _ in range(self.CLOSED_BILLS_SECOND_DAY):
            baker.make(
                "order.Bill",
                created_at=self.SECOND_DAY_CREATED_AT,
                status=StatusBill.CLOSED,
            )

    def test_count_bill_status(self):
        """Test counting bills by status for a given date."""
        count_bill = CountBillStatus()
        self.assertEqual(
            count_bill.calculate(self.FIRST_DAY_CREATED_AT, self.SECOND_DAY_CREATED_AT),
            {"opened": self.OPEN_BILLS, "closed": self.CLOSED_BILLS_FIRST_DAY},
        )
