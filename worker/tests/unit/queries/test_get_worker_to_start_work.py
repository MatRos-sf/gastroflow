from datetime import timedelta

from model_bakery import baker

from worker.queries import get_workers_not_clocked_in_today

from . import MOCK_NOW, BaseWorkerQueryTest, make_worker_dict


class GetWorkersNotClockedInTodayTest(BaseWorkerQueryTest):
    def test_worker_with_no_worktime_is_returned(self):
        worker = baker.make("worker.Worker")

        result = get_workers_not_clocked_in_today()

        self.assertIn(make_worker_dict(worker), result)
        self.assertEqual(result.count(), 1)

    def test_worker_who_finished_shift_today_is_returned(self):
        worker = baker.make("worker.Worker")
        baker.make(
            "worker.WorkTime",
            worker=worker,
            start_time=MOCK_NOW - timedelta(hours=2),
            finish_time=MOCK_NOW - timedelta(hours=1),
        )

        result = get_workers_not_clocked_in_today()

        self.assertIn(make_worker_dict(worker), result)
        self.assertEqual(result.count(), 1)

    def test_worker_with_multiple_finished_shifts_today_returned_once(self):
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
            finish_time=MOCK_NOW - timedelta(hours=3),
        )

        result = get_workers_not_clocked_in_today()

        self.assertIn(make_worker_dict(worker), result)
        self.assertEqual(result.count(), 1)

    def test_worker_currently_clocked_in_is_excluded(self):
        worker = baker.make("worker.Worker")
        baker.make(
            "worker.WorkTime",
            worker=worker,
            start_time=MOCK_NOW - timedelta(hours=1),
            finish_time=None,
        )

        result = get_workers_not_clocked_in_today()

        self.assertNotIn(make_worker_dict(worker), result)
        self.assertEqual(result.count(), 0)

    def test_multiple_workers_not_clocked_in_are_returned(self):
        baker.make("worker.Worker", first_name="Tom")
        baker.make("worker.Worker", first_name="Dick")

        result = get_workers_not_clocked_in_today()

        self.assertEqual(result.count(), 2)
