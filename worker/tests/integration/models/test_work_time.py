from decimal import Decimal

from django.test import TestCase
from model_bakery import baker

from worker.models import Worker, WorkTime


class WorkTimeTest(TestCase):
    def test_should_set_properly_snapshot_salary(self):
        salary = Decimal(50)
        worker = baker.make(Worker, salary=salary)
        work_time = baker.make(WorkTime, worker=worker)

        self.assertEqual(worker.salary, work_time.salary_snapshot)

    def test_salary_snapshot_does_not_change_when_worker_salary_updates(self):
        worker = baker.make(Worker, salary=Decimal(50))
        work_time = baker.make(WorkTime, worker=worker)

        worker.salary = Decimal(100)
        worker.save()
        work_time.refresh_from_db()

        self.assertEqual(work_time.salary_snapshot, Decimal(50))
