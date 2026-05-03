from django.utils import timezone

from .models import WorkTime


def settle_work_times(work_time_ids: list[int]) -> None:
    WorkTime.objects.filter(
        pk__in=work_time_ids,
        is_settled=False,
        finish_time__isnull=False,
    ).update(is_settled=True, settled_at=timezone.now())


def unsettle_work_times(work_time_ids: list[int]) -> None:
    WorkTime.objects.filter(
        pk__in=work_time_ids,
        is_settled=True,
    ).update(is_settled=False, settled_at=None)
