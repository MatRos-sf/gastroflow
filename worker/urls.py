from django.urls import path

from .views import (
    ClockInActionView,
    ClockInView,
    ClockOutActionView,
    ClockOutView,
    SettlementRowsView,
    SettlementSummaryView,
    SettlementUndoView,
    SettlementView,
    WorkerCreateView,
    WorkerDetailView,
    WorkerListView,
    WorkerUpdateView,
    WorkerWorkTimeListView,
    WorkTimeNotFinishedListView,
    WorkTimeUpdateView,
)

app_name = "gf-worker"

urlpatterns = [
    path("create/", WorkerCreateView.as_view(), name="worker-create"),
    path("list/", WorkerListView.as_view(), name="worker-list"),
    path("<int:pk>/", WorkerDetailView.as_view(), name="worker-detail"),
    path("<int:pk>/update/", WorkerUpdateView.as_view(), name="worker-update"),
    path(
        "<int:pk>/worktimes/", WorkerWorkTimeListView.as_view(), name="worker-worktimes"
    ),
    path(
        "worktime/<int:pk>/update/",
        WorkTimeUpdateView.as_view(),
        name="worktimes-update",
    ),
    path(
        "worktime/not-finished/",
        WorkTimeNotFinishedListView.as_view(),
        name="worktime-not-finished",
    ),
    path("settlements/", SettlementView.as_view(), name="settlement-list"),
    path("settlements/rows/", SettlementRowsView.as_view(), name="settlement-rows"),
    path(
        "settlements/summary/",
        SettlementSummaryView.as_view(),
        name="settlement-summary",
    ),
    path("settlements/undo/", SettlementUndoView.as_view(), name="settlement-undo"),
    path("clock-in/", ClockInView.as_view(), name="worker-clock-in"),
    path(
        "clock-in/<int:pk>/start/",
        ClockInActionView.as_view(),
        name="worker-clock-in-start",
    ),
    path("clock-out/", ClockOutView.as_view(), name="worker-clock-out"),
    path(
        "clock-out/<int:pk>/end/",
        ClockOutActionView.as_view(),
        name="worker-clock-out-end",
    ),
]
