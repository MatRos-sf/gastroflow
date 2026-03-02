from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase


class CreateUsersCommandTests(TestCase):
    def test_creates_both_users(self):
        out = StringIO()
        call_command(
            "create_users",
            boss_username="boss",
            boss_password="pass",
            workers_username="worker",
            workers_password="pass",
            stdout=out,
        )
        self.assertEqual(User.objects.count(), 2)

    def test_skips_existing_user(self):
        User.objects.create_user("boss", password="old")
        out = StringIO()
        call_command(
            "create_users",
            boss_username="boss",
            boss_password="new",
            workers_username="worker",
            workers_password="pass",
            stdout=out,
        )
        self.assertIn("already exists", out.getvalue())
        self.assertEqual(User.objects.count(), 2)
