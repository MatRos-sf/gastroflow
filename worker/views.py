from django.views.generic import CreateView

from .forms import WorkerForm
from .models import Worker


class CreateWorkerView(CreateView):
    model = Worker
    form_class = WorkerForm
    template_name = "worker/create-worker.html"
