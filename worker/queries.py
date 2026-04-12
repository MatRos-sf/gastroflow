from datetime import date

from django.db.models import QuerySet
from django.utils import timezone

from worker.models import Worker, WorkTime


def get_workers_not_clocked_in_today() -> QuerySet[dict]:
    """
    Return workers who have not started work today, or finished their shift and can clock in again.
    """
    date_now = timezone.now().date()
    workers = (
        Worker.objects.exclude(
            worktime__start_time__date=date_now, worktime__finish_time__isnull=True
        )
        .distinct()
        .values("pk", "first_name", "last_name")
    )

    return workers


def get_workers_clocked_in_today(values: list[str] | None = None) -> QuerySet[dict]:
    """
    Return workers who have started work today and have not finished their shift.
    Pass a custom `values` list to select specific fields (default: pk, first_name, last_name).
    """
    date_now = timezone.now().date()
    if not values:
        values = ["pk", "first_name", "last_name"]
    workers = (
        Worker.objects.filter(
            worktime__start_time__date=date_now, worktime__finish_time__isnull=True
        )
        .distinct()
        .values(*values)
    )

    return workers


def get_workers_with_unsettled_work_times() -> QuerySet[Worker]:
    return (
        Worker.objects.filter(
            worktime__is_settled=False,
            worktime__finish_time__isnull=False,
        )
        .distinct()
        .order_by("first_name", "last_name")
    )


def get_unsettled_work_times(
    worker_pk: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> QuerySet[WorkTime]:
    qs = WorkTime.objects.filter(
        is_settled=False,
        finish_time__isnull=False,
    ).select_related("worker")

    if worker_pk is not None:
        qs = qs.filter(worker__pk=worker_pk)
    if date_from is not None:
        qs = qs.filter(start_time__date__gte=date_from)
    if date_to is not None:
        qs = qs.filter(start_time__date__lte=date_to)

    return qs.order_by("worker__first_name", "start_time")
