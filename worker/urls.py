from django.urls import path

from .views import CreateWorkerView

app_name = "gf-worker"

urlpatterns = [path("create/", CreateWorkerView.as_view(), name="worker-create")]
