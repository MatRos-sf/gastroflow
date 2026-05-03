from django.conf import settings
from django.http import HttpRequest
from django.test import TestCase
from django.utils.module_loading import import_module
from faker import Faker
from parameterized import parameterized

from tools.session import clear_session

NUMBER_OF_SESSION_KEYS = 3


class ClearSessionTest(TestCase):
    FAKE = Faker()

    def setUp(self):
        super().setUp()
        self.request = HttpRequest()

        engine = import_module(settings.SESSION_ENGINE)
        self.request.session = engine.SessionStore()

        self.session_keys = [f"session{i}" for i in range(NUMBER_OF_SESSION_KEYS)]
        for field in self.session_keys:
            self.request.session[field] = self.FAKE

    def test_clear_session(self):
        clear_session(self.request, self.session_keys)
        for key in self.session_keys:
            self.assertNotIn(key, self.request.session)

    @parameterized.expand(
        [(i, NUMBER_OF_SESSION_KEYS - i) for i in range(NUMBER_OF_SESSION_KEYS + 1)]
    )
    def test_should_remove_only_specified_keys(self, to_remove, expected_no):
        keys = self.session_keys[:to_remove]
        clear_session(self.request, keys)

        # count existing keys
        existing_keys = 0
        for key in self.session_keys:
            if self.request.session.get(key):
                existing_keys += 1
        self.assertEqual(existing_keys, expected_no)
