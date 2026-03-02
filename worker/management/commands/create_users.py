"""
Management command: create_users
=================================
Creates the two application-level user accounts required for the system to operate:
    - Boss (superuser):
        Manages workers, orders, and menu items.
        Has all Worker permissions.

    - Worker (shared account with actor tracking):
        Processes orders, updates dish statuses, and closes bills.

Usage:
  python manage.py create_users
  python manage.py create_users --BOSS_USERNAME admin --BOSS_PASSWORD secret

Configuration:
  Credentials are read from environment variables by default:
      BOSS_USERNAME, BOSS_PASSWORD
      WORKERS_USERNAME, WORKERS_PASSWORD

  All values can be overridden via CLI arguments (see --help).
"""
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction


@transaction.atomic
def create_app_user(username: str, password: str, is_superuser: bool) -> bool:
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_password(password)
        user.is_superuser = is_superuser
        user.save()

    return created


class Command(BaseCommand):
    help = "Create basic users (Boss and Worker). You can override default values with arguments."

    def add_arguments(self, parser):
        parser.add_argument(
            "--boss_username",
            type=str,
            default=settings.BOSS_USERNAME,
            help="Boss username.",
            required=False,
        )
        parser.add_argument(
            "--boss_password",
            type=str,
            default=settings.BOSS_PASSWORD,
            help="Boss password.",
            required=False,
        )
        parser.add_argument(
            "--workers_username",
            type=str,
            default=settings.WORKERS_USERNAME,
            help="Worker username.",
            required=False,
        )
        parser.add_argument(
            "--workers_password",
            type=str,
            default=settings.WORKERS_PASSWORD,
            help="Worker password.",
            required=False,
        )

    def _try_create_user(self, is_superuser: bool) -> None:
        if is_superuser:
            user_name = self.username_boss
            password = self.password_boss
        else:
            user_name = self.username_worker
            password = self.password_worker

        if not user_name or not password:
            self.stdout.write(self.style.ERROR("User name or password is empty"))
            self.stdout.write(self.style.WARNING("The script will exit"))
            return

        created = create_app_user(user_name, password, is_superuser)

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created user {user_name}"))
        else:
            self.stdout.write(self.style.WARNING(f"User {user_name} already exists"))

    def handle(self, *args, **options):
        self.username_boss = options["boss_username"]
        self.password_boss = options["boss_password"]
        self.username_worker = options["workers_username"]
        self.password_worker = options["workers_password"]

        self._try_create_user(True)
        self._try_create_user(False)
