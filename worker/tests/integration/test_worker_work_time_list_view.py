from datetime import datetime, timezone
from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from worker.models import Worker, WorkTime


def url(pk):
    return reverse("gf-worker:worker-detail", kwargs={"pk": pk})


class WorkerDetailViewTest(TestCase):
    def setUp(self):
        self.worker = baker.make(Worker)

    # --- HTTP / routing ---
    def test_returns_200_for_existing_worker(self):
        response = self.client.get(url(self.worker.pk))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # --- Context: page_obj ---

    def test_page_obj_contains_only_this_workers_worktimes(self):
        baker.make(WorkTime, worker=self.worker, _quantity=3)
        other_worker = baker.make(Worker)
        baker.make(WorkTime, worker=other_worker, _quantity=2)

        response = self.client.get(url(self.worker.pk))
        self.assertEqual(len(response.context["page_obj"]), 3)

    def test_page_obj_is_ordered_by_start_time_descending(self):
        t1 = baker.make(
            WorkTime,
            worker=self.worker,
            start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        t2 = baker.make(
            WorkTime,
            worker=self.worker,
            start_time=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )

        response = self.client.get(url(self.worker.pk))
        page = list(response.context["page_obj"])
        self.assertEqual(page[0], t2)
        self.assertEqual(page[1], t1)

    # --- Context: total_duration ---

    def test_total_duration_is_none_when_no_worktimes(self):
        response = self.client.get(url(self.worker.pk))
        self.assertIsNone(response.context["total_duration"])

    def test_total_duration_is_correct_sum(self):
        baker.make(
            WorkTime,
            worker=self.worker,
            start_time=datetime(2024, 1, 1, 8, 0, tzinfo=timezone.utc),
            finish_time=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),  # 2h
        )
        baker.make(
            WorkTime,
            worker=self.worker,
            start_time=datetime(2024, 1, 2, 8, 0, tzinfo=timezone.utc),
            finish_time=datetime(2024, 1, 2, 11, 0, tzinfo=timezone.utc),  # 3h
        )

        response = self.client.get(url(self.worker.pk))
        from datetime import timedelta

        self.assertEqual(response.context["total_duration"], timedelta(hours=5))
