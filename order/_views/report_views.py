from datetime import datetime
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import View

from order.report import generate_summary_report
from tools.report_calculator import CALCULATOR_BASIC


class ReportDispatchView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return ReportView.as_view()(request, *args, **kwargs)
        return ReportBasicView.as_view()(request, *args, **kwargs)


class ReportBasicView(View):
    template_name = "order/report/report_base.html"
    calculator_collection = CALCULATOR_BASIC

    def build_context(
        self, from_date: datetime | None, to_date: datetime | None
    ) -> dict[str, Any]:
        return {
            "date_from": from_date,
            "date_to": to_date,
            "report": generate_summary_report(
                from_date, to_date, self.calculator_collection
            ),
        }

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        return render(request, self.template_name, self.build_context(today, None))


class ReportView(ReportBasicView):
    template_name = "order/report/report_base.html"
