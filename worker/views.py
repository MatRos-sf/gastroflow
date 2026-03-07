from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from tools.models.aggregate import total_work_duration

from .forms import WorkerForm, WorkTimeForm
from .models import Worker, WorkTime
from .queries import get_workers_clocked_in_today, get_workers_not_clocked_in_today

PAGE_SIZE = 10


class WorkerCreateView(UserPassesTestMixin, CreateView):
    model = Worker
    form_class = WorkerForm
    template_name = "worker/create-worker.html"

    def test_func(self) -> bool:
        return self.request.user.is_superuser


class WorkerDetailView(LoginRequiredMixin, DetailView):
    model = Worker
    template_name = "worker/detail-worker.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.object.worktime_set.order_by("-start_time")
        paginator = Paginator(qs, PAGE_SIZE)
        context["page_obj"] = paginator.get_page(1)
        context["total_duration"] = total_work_duration(self.object.worktime_set)
        return context


class WorkerWorkTimeListView(LoginRequiredMixin, ListView):
    template_name = "worker/_worktime_rows.html"
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        self.worker = get_object_or_404(Worker, pk=self.kwargs["pk"])
        return self.worker.worktime_set.order_by("-start_time")


class WorkerListView(LoginRequiredMixin, ListView):
    model = Worker
    template_name = "worker/list-worker.html"


class WorkerUpdateView(UserPassesTestMixin, UpdateView):
    model = Worker
    form_class = WorkerForm
    template_name = "worker/update-worker.html"

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, _("Worker detail has been updated!"))
        return super().form_valid(form)


class WorkTimeUpdateView(UserPassesTestMixin, UpdateView):
    model = WorkTime
    form_class = WorkTimeForm
    template_name = "worker/update-work-time.html"

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, _("Work time has been successfully updated!"))
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.worker.get_absolute_url()


class ClockInView(LoginRequiredMixin, TemplateView):
    template_name = "worker/clock-in.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workers"] = get_workers_not_clocked_in_today()
        return context


class ClockInActionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        worker = get_object_or_404(Worker, pk=self.kwargs["pk"])
        WorkTime.objects.create(worker=worker, start_time=timezone.now())
        messages.success(
            request, _("Have a great shift, %(name)s!") % {"name": worker.first_name}
        )

        return redirect("gf-worker:worker-clock-in")


class ClockOutView(LoginRequiredMixin, TemplateView):
    template_name = "worker/clock-out.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workers"] = get_workers_clocked_in_today()
        return context


class ClockOutActionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        worker = get_object_or_404(Worker, pk=self.kwargs["pk"])

        dt_now = timezone.now()
        wt = get_object_or_404(
            WorkTime,
            worker=worker,
            start_time__date=dt_now.date(),
            finish_time__isnull=True,
        )
        wt.finish_time = dt_now
        wt.save()

        messages.success(request, _("Goodbye, %(name)s!") % {"name": worker.first_name})

        return redirect("gf-worker:worker-clock-out")
