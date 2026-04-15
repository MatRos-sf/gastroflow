import base64
import logging
import os
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import requests
from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.utils import timezone

from order.models import Bill, BillReceipt
from order.queries import get_order_additions_detail, get_order_items_detail
from tools.converter import convert_date_from_str_to_date
from tools.spreadsheet.sheets.order_detail import OrderAdditionSheet, OrderItemSheet
from tools.spreadsheet.spreadsheet import ManagerSpreadsheet

logger = logging.getLogger(__name__)


def _build_report_subject(from_date: date | None, to_date: date | None) -> str:
    if from_date and to_date:
        return f"Order Report {from_date.strftime('%d.%m.%Y')} - {to_date.strftime('%d.%m.%Y')}"
    if from_date:
        return f"Order Report from {from_date.strftime('%d.%m.%Y')}"
    if to_date:
        return f"Order Report up to {to_date.strftime('%d.%m.%Y')}"
    return "Order Report (all time)"


@shared_task
def generate_report_and_send_email_task(
    from_date: str | None, to_date: str | None
) -> str:
    """Generate Excel report and send via email to all staff users."""
    from_date_obj = convert_date_from_str_to_date(from_date) if from_date else None
    to_date_obj = convert_date_from_str_to_date(to_date, False) if to_date else None

    logger.info(f"Generating report: from={from_date_obj} to={to_date_obj}")

    recipient_emails = list(
        User.objects.filter(is_staff=True, is_active=True)
        .values_list("email", flat=True)
        .exclude(email="")
    )

    if not recipient_emails:
        logger.warning("No staff users with email found")
        return "No recipients found"

    subject = _build_report_subject(
        from_date_obj.date() if from_date_obj else None,
        to_date_obj.date() if to_date_obj else None,
    )
    body = f"{subject}."

    items = get_order_items_detail(
        from_date_obj.date() if from_date_obj else None,
        to_date_obj.date() if to_date_obj else None,
    )
    additions = get_order_additions_detail(
        from_date_obj.date() if from_date_obj else None,
        to_date_obj.date() if to_date_obj else None,
    )

    date_from_str = from_date_obj.date().strftime("%d.%m.%Y") if from_date_obj else None
    date_to_str = to_date_obj.date().strftime("%d.%m.%Y") if to_date_obj else None

    mail = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.EMAIL_HOST_USER,
        to=recipient_emails,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        excel_path = os.path.join(
            tmpdir,
            ManagerSpreadsheet.create_report_name(from_date_obj, to_date_obj),
        )
        spreadsheet = ManagerSpreadsheet(excel_path)
        spreadsheet.add_sheet(
            "order_items",
            OrderItemSheet,
            items,
            date_from=date_from_str,
            date_to=date_to_str,
        )
        spreadsheet.add_sheet(
            "order_additions",
            OrderAdditionSheet,
            additions,
            date_from=date_from_str,
            date_to=date_to_str,
        )
        spreadsheet.save()

        with open(excel_path, "rb") as excel_file:
            mail.attach(
                filename=Path(excel_path).name,
                content=excel_file.read(),
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        mail.send(fail_silently=False)

    logger.info(f"Report sent to {len(recipient_emails)} recipients")
    return f"Report sent to {len(recipient_emails)} users"


class BillBuilder:
    DEFAULT_DISCOUNT_NAME = "Promo"

    def __init__(self, bill_pk: int):
        self._bill = Bill.objects.get(pk=bill_pk)
        self._bill_payload = dict()
        self._sum_bill = 0  # sum of all lines without discount
        self._discount = 0

        self.endpoint = ""

    def prepare_lines(self):
        lines = []
        orders = self._bill.orders.all()

        for order in orders:
            for item in order.order_items.all():
                quantity = item.quantity
                lines.append(
                    {
                        "na": item.item.bill_name,
                        "il": quantity,
                        "vt": item.item.vat.value,
                        "pr": int(item.price_snapshot * Decimal(100)),
                    }
                )
                self._sum_bill += int(quantity * item.price_snapshot * Decimal(100))
                for addition in item.order_item_additions.all():
                    quantity = addition.quantity
                    lines.append(
                        {
                            "na": addition.addition.bill_name,
                            "il": quantity,
                            "vt": addition.addition.vat.value,
                            "pr": int(addition.price_snapshot * Decimal(100)),
                        }
                    )
                    self._sum_bill += int(
                        quantity * addition.price_snapshot * Decimal(100)
                    )

        self._bill_payload["lines"] = lines

    def prepare_discount(self):
        discount = self._bill.discount
        if not discount:
            return
        self._discount = discount
        self._bill_payload["discounts"] = [
            {
                "type": "bill",
                "discount": {
                    "na": f"{self.DEFAULT_DISCOUNT_NAME} {discount*100}",
                    "rd": True,
                    "rp": int(discount * 100),
                },
            }
        ]

    def prepare_summary(self):
        total = int(self._sum_bill * (1 - Decimal(self._discount) / 100))
        self._bill_payload["summary"] = {"to": total}

    def prepare_simulation(self):
        if not settings.POSNET_SIMULATION:
            return
        waiter_name = ""
        if self._bill.waiter:
            waiter = self._bill.waiter
            waiter_name = f"{waiter.first_name} {waiter.last_name}".strip()
        self._bill_payload["simulation"] = {
            "parameters": {
                "header": {
                    "company": settings.POSNET_COMPANY,
                    "address": settings.POSNET_ADDRESS,
                },
                "footer": {
                    "cashier": waiter_name,
                    "billNumber": self._bill.pk,
                },
                "fiscal": True,
            },
        }

    def prepare_extralines(self):
        extralines = [{"id": 2, "na": str(self._bill.pk)}]
        if self._bill.waiter:
            waiter = self._bill.waiter
            extralines.append(
                {"id": 15, "na": f"{waiter.first_name} {waiter.last_name}".strip()}
            )
        self._bill_payload["extralines"] = extralines

    def create_payload(self):
        self.prepare_lines()
        self.prepare_discount()
        self.prepare_summary()
        self.prepare_extralines()
        self.prepare_simulation()

    def send(self) -> dict:
        url = f"{settings.POSNET_URL}/paragon"
        params = {"simulation": "true"} if settings.POSNET_SIMULATION else {}

        response = requests.post(
            url, json=self._bill_payload, params=params, timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if settings.POSNET_SIMULATION:
            image_data = data.get("imageData")
            if image_data:
                bills_dir = Path(settings.POSNET_DEV_BILLS_DIR)
                bills_dir.mkdir(parents=True, exist_ok=True)
                filepath = bills_dir / f"bill_{self._bill.pk}.png"
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(image_data))
                logger.info(f"Simulation receipt saved: {filepath}")
            else:
                logger.warning(
                    f"Simulation mode but no imageData in response for bill {self._bill.pk}"
                )

        return data


@shared_task
def finalize_bill(bill_pk: int):
    builder = BillBuilder(bill_pk)
    builder.create_payload()
    response = builder.send()

    BillReceipt.objects.create(
        bill_id=bill_pk,
        ok=response.get("ok", False),
        hn=response.get("hn", ""),
        bn=response.get("bn", ""),
        took=response.get("took", 0),
        raw_response=response,
    )

    Bill.objects.filter(pk=bill_pk).update(
        is_printed=True,
        printed_at=timezone.now(),
    )

    logger.info(
        f"Bill {bill_pk} finalized: ok={response.get('ok')}, hn={response.get('hn')}"
    )
