from django.test import TestCase

from order.factories import BillMixinFactory
from order.models import Bill


class TestBillFactory(BillMixinFactory, TestCase):
    def test_should_create_bill(self):
        bill = self.make_bill()
        self.assertIsInstance(bill, Bill)

    def test_should_create_3_bills(self):
        self.make_bill(_quantity=3)
        self.assertEqual(Bill.objects.count(), 3)

    def test_should_create_bill_with_discount(self):
        bill = self.make_bill(discount=10)
        self.assertEqual(bill.discount, 10)
