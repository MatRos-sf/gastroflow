from django.urls import path

from .views import (
    WorkerCreateView,
    WorkerDetailView,
    WorkerWorkTimeListView,
    WorkTimeUpdateView,
)

app_name = "gf-worker"

urlpatterns = [
    path("create/", WorkerCreateView.as_view(), name="worker-create"),
    path("<int:pk>/", WorkerDetailView.as_view(), name="worker-detail"),
    path(
        "<int:pk>/worktimes/", WorkerWorkTimeListView.as_view(), name="worker-worktimes"
    ),
    path(
        "worktime/<int:pk>/update/",
        WorkTimeUpdateView.as_view(),
        name="worktimes-update",
    ),
]
