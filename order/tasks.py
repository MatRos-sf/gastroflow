import logging
import os
import tempfile
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from model_utils import get_order_additions_summary, get_order_items_summary
from order.raport import generate_summary_report
from tools.converter import convert_date_from_str_to_date
from tools.raport_calculator import CALCULATOR_COLLECTION
from tools.report_generator import GenerateReport
from tools.spreadsheet.spreadsheet import ManagerSpreadsheet

logger = logging.getLogger(__name__)


@shared_task
def generate_report_and_send_email_task(from_date: str, to_date: str):
    """Generate Excel report and send via email to all staff users."""
    from_date_obj = convert_date_from_str_to_date(from_date)
    to_date_obj = convert_date_from_str_to_date(to_date, False)
    logger.info(f"Generating report for {from_date_obj.date()} to {to_date_obj.date()}")
    context = {
        "report": generate_summary_report(
            from_date_obj, to_date_obj, CALCULATOR_COLLECTION
        ),
        "table_report_items": get_order_items_summary(from_date_obj, to_date_obj),
        "table_report_additions": get_order_additions_summary(
            from_date_obj, to_date_obj
        ),
    }

    recipient_emails = list(
        User.objects.filter(is_staff=True, is_active=True)
        .values_list("email", flat=True)
        .exclude(email="")
    )

    if not recipient_emails:
        logger.warning("No staff users with email found")
        return "No recipients found"

    text_content = render_to_string("emails/report_email.txt", context)

    subject = f"Raport Zamówień {from_date_obj.date().strftime('%d.%m.%Y')} - {to_date_obj.date().strftime('%d.%m.%Y')}"

    mail = EmailMessage(
        subject=subject,
        body=text_content,
        from_email=settings.EMAIL_HOST_USER,
        to=recipient_emails,
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        excel_path = os.path.join(
            tmpdir, ManagerSpreadsheet.create_report_name(from_date_obj, to_date_obj)
        )
        gen = GenerateReport(ManagerSpreadsheet(excel_path))

        gen.generate_report_from_context(context)

        with open(excel_path, "rb") as excel_file:
            mail.attach(
                filename=Path(excel_path).name,
                content=excel_file.read(),
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        mail.send(fail_silently=False)

        logger.info(f"Report sent successfully to {len(recipient_emails)} recipients")
        return f"Report sent to {len(recipient_emails)} users"
