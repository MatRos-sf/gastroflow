from typing import TypedDict, Unpack

from model_bakery import baker

from order.models import Bill, PaymentMethod, StatusBill


class BillKwargs(TypedDict, total=False):
    _quantity: int
    status: StatusBill
    discount: int
    payment_method: PaymentMethod
    guest_count: int
    note: str


class BillMixinFactory:
    def make_bill(self, **kwargs: Unpack[BillKwargs]) -> Bill:
        return baker.make(Bill, **kwargs)
