from datetime import timedelta

from django.db.models import DurationField, ExpressionWrapper, F, Sum

from worker.models import WorkTime


def total_work_duration(qs: WorkTime) -> timedelta | None:
    return qs.filter(finish_time__isnull=False).aggregate(
        total=Sum(
            ExpressionWrapper(
                F("finish_time") - F("start_time"), output_field=DurationField()
            )
        )
    )["total"]
