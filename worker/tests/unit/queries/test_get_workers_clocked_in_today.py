from datetime import timedelta

from model_bakery import baker

from worker.queries import get_workers_clocked_in_today

from . import MOCK_NOW, BaseWorkerQueryTest, make_worker_dict


class GetWorkersClockedInTodayTest(BaseWorkerQueryTest):
    def test_worker_with_no_worktime_is_excluded(self):
        baker.make("worker.Worker")

        result = get_workers_clocked_in_today()

        self.assertEqual(result.count(), 0)

    def test_worker_who_started_shift_today_is_returned(self):
        worker = baker.make("worker.Worker")
        baker.make(
            "worker.WorkTime",
            worker=worker,
            start_time=MOCK_NOW - timedelta(hours=2),
        )

        result = get_workers_clocked_in_today()

        self.assertIn(make_worker_dict(worker), result)
        self.assertEqual(result.count(), 1)

    def test_worker_who_returned_after_finishing_is_included(self):
        worker = baker.make("worker.Worker")
        baker.make(
            "worker.WorkTime",
            worker=worker,
            start_time=MOCK_NOW - timedelta(hours=6),
            finish_time=MOCK_NOW - timedelta(hours=5),
        )
        baker.make(
            "worker.WorkTime",
            worker=worker,
            start_time=MOCK_NOW - timedelta(hours=4),
        )

        result = get_workers_clocked_in_today()

        self.assertIn(make_worker_dict(worker), result)
        self.assertEqual(result.count(), 1)

    def test_multiple_clocked_in_workers_are_returned(self):
        tom = baker.make("worker.Worker", first_name="Tom")
        dick = baker.make("worker.Worker", first_name="Dick")
        baker.make(
            "worker.WorkTime", worker=tom, start_time=MOCK_NOW - timedelta(hours=1)
        )
        baker.make(
            "worker.WorkTime", worker=dick, start_time=MOCK_NOW - timedelta(hours=1)
        )

        result = get_workers_clocked_in_today()

        self.assertIn(make_worker_dict(tom), result)
        self.assertIn(make_worker_dict(dick), result)
        self.assertEqual(result.count(), 2)

    def test_worker_from_yesterday_with_open_shift_is_excluded(self):
        worker = baker.make("worker.Worker")
        baker.make(
            "worker.WorkTime",
            worker=worker,
            start_time=MOCK_NOW - timedelta(hours=26),
        )
        baker.make(
            "worker.WorkTime",
            worker=worker,
            start_time=MOCK_NOW - timedelta(hours=2),
            finish_time=MOCK_NOW - timedelta(hours=1),
        )

        result = get_workers_clocked_in_today()

        self.assertEqual(result.count(), 0)
