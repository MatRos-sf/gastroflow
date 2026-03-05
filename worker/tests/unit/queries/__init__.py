from datetime import date, datetime
from datetime import timezone as dt_timezone
from unittest.mock import patch

from django.test import TestCase

MOCK_TODAY = date(2026, 3, 5)
MOCK_NOW = datetime(2026, 3, 5, 12, 0, 0, tzinfo=dt_timezone.utc)


def make_worker_dict(worker) -> dict[str, str | int]:
    return {
        "pk": worker.pk,
        "first_name": worker.first_name,
        "last_name": worker.last_name,
    }


class BaseWorkerQueryTest(TestCase):
    def setUp(self):
        self._tz_patcher = patch("worker.queries.timezone")
        mock_tz = self._tz_patcher.start()
        mock_tz.now.return_value = MOCK_NOW

    def tearDown(self):
        self._tz_patcher.stop()
