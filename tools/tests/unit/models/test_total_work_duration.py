import datetime

from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from tools.models.aggregate import total_work_duration
from worker.models import WorkTime


class TotalWorkDurationTest(TestCase):
    def make_work_time(self, **kwargs) -> WorkTime:
        return baker.make(WorkTime, **kwargs)

    def test_total_duration_all_workers(self):
        self.make_work_time(
            start_time=timezone.make_aware(datetime.datetime(2026, 1, 1, 7, 0)),
            finish_time=timezone.make_aware(datetime.datetime(2026, 1, 1, 16, 0)),  # 9h
        )
        self.make_work_time(
            start_time=timezone.make_aware(datetime.datetime(2026, 1, 2, 7, 0)),
            finish_time=timezone.make_aware(datetime.datetime(2026, 1, 2, 16, 0)),  # 9h
        )
        total = total_work_duration(WorkTime.objects.all())
        self.assertEqual(total, datetime.timedelta(hours=18))

    def test_returns_none_when_queryset_is_empty(self):
        total = total_work_duration(WorkTime.objects.all())
        self.assertIsNone(total)
