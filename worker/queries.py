from django.db.models import QuerySet
from django.utils import timezone

from worker.models import Worker


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
