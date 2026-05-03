from django.contrib.auth.models import User
from django.test import TestCase

from worker.management.commands.create_users import create_app_user


class CreateAppUserTest(TestCase):
    def test_creates_user_and_returns_true(self):
        created = create_app_user("alice", "secret", is_superuser=False)
        self.assertTrue(created)
        self.assertTrue(User.objects.filter(username="alice").exists())

    def test_returns_false_when_user_exists(self):
        User.objects.create_user("alice", password="old")
        created = create_app_user("alice", "new", is_superuser=False)
        self.assertFalse(created)

    def test_superuser_flag(self):
        create_app_user("boss", "secret", is_superuser=True)
        user = User.objects.get(username="boss")
        self.assertTrue(user.is_superuser)
