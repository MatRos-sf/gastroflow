from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone
from parameterized import parameterized

from worker.forms import WorkTimeForm

TEST_DATE = timezone.make_aware(datetime(2026, 3, 9, 7, 0))


class WorkTimeFormTest(TestCase):
    def _valid_data(self, **kwargs):
        data = {
            "start_time": TEST_DATE,
            "salary_snapshot": "25.00",
        }
        data.update(kwargs)
        return data

    def test_valid_form(self):
        form = WorkTimeForm(data=self._valid_data())
        self.assertTrue(form.is_valid())

    def test_worker_field_excluded(self):
        form = WorkTimeForm()
        self.assertNotIn("worker", form.fields)

    def test_finish_time_is_optional(self):
        form = WorkTimeForm(data=self._valid_data(finish_time=""))
        self.assertTrue(form.is_valid())

    @parameterized.expand(["start_time", "salary_snapshot"])
    def test_required_field(self, field_name):
        data = self._valid_data()
        del data[field_name]
        form = WorkTimeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(field_name, form.errors)

    def test_invalid_salary_snapshot(self):
        form = WorkTimeForm(data=self._valid_data(salary_snapshot="not_a_number"))
        self.assertFalse(form.is_valid())
        self.assertIn("salary_snapshot", form.errors)

    @parameterized.expand(
        [
            ("equal", TEST_DATE),
            ("less_one_min", TEST_DATE - timedelta(minutes=1)),
            ("less_one_hour", TEST_DATE - timedelta(hours=1)),
            ("less_one_day", TEST_DATE - timedelta(days=1)),
        ]
    )
    def test_finish_date_should_be_gt_than_start_time(self, name, date):
        form = WorkTimeForm(self._valid_data(finish_time=date))
        self.assertFalse(form.is_valid())
