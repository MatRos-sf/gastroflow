from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.generic import View

from order.forms import DateForm
from order.report import generate_summary_report
from order.tasks import generate_report_and_send_email_task
from tools.report_calculator import CALCULATOR_BASIC, CALCULATOR_COLLECTION


class ReportBasicView(View):
    template_name = "order/report/report_base.html"
    calculator_collection = CALCULATOR_BASIC

    def build_context(self, from_date, to_date) -> dict[str, Any]:
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
    template_name = "order/report/report.html"
    calculator_collection = CALCULATOR_COLLECTION

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        form = DateForm(request.GET or None)

        if request.GET and form.is_valid():
            from_date = form.cleaned_data.get("from_date")
            to_date = form.cleaned_data.get("to_date")
            if to_date and not from_date:
                from_date = today
        else:
            from_date = today
            to_date = None
            form = DateForm(initial={"from_date": from_date})

        context = self.build_context(from_date, to_date)
        context["form"] = form
        return render(request, self.template_name, context)


class ReportDispatchView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return ReportView.as_view()(request, *args, **kwargs)
        return ReportBasicView.as_view()(request, *args, **kwargs)


@login_required
@require_POST
def generate_report_view(request):
    from_date = request.POST.get("from_date") or None
    to_date = request.POST.get("to_date") or None
    generate_report_and_send_email_task.delay(from_date, to_date)
    messages.success(request, _("Report is being generated. It will be sent to email."))
    return redirect("report")
