from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.views.generic import CreateView, DetailView, ListView

from tools.models.aggregate import total_work_duration

from .forms import WorkerForm
from .models import Worker

PAGE_SIZE = 10


class WorkerCreateView(CreateView):
    model = Worker
    form_class = WorkerForm
    template_name = "worker/create-worker.html"


class WorkerDetailView(DetailView):
    model = Worker
    template_name = "worker/detail-worker.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.object.worktime_set.order_by("-start_time")
        paginator = Paginator(qs, PAGE_SIZE)
        context["page_obj"] = paginator.get_page(1)
        context["total_duration"] = total_work_duration(self.object.worktime_set)
        return context


class WorkerWorkTimeListView(ListView):
    template_name = "worker/_worktime_rows.html"
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        self.worker = get_object_or_404(Worker, pk=self.kwargs["pk"])
        return self.worker.worktime_set.order_by("-start_time")
