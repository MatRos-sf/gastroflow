import logging
import os
import tempfile
from datetime import date
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage

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
