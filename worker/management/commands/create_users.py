from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction


@transaction.atomic
def create_app_user(
    username: str, password: str, is_superuser: bool, email: str | None = None
) -> bool:
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_password(password)
        user.is_superuser = is_superuser
        if is_superuser:
            user.email = email
            user.is_staff = True
        user.save()

    return created


class Command(BaseCommand):
    help = "Create basic users (Boss and Worker)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--boss_username",
            type=str,
            help="Boss username.",
            required=False,
        )
        parser.add_argument(
            "--boss_password",
            type=str,
            help="Boss password.",
            required=False,
        )
        parser.add_argument(
            "--boss_email",
            type=str,
            help="Boss email.",
            required=False,
        )
        parser.add_argument(
            "--workers_username",
            type=str,
            help="Worker username.",
            required=False,
        )
        parser.add_argument(
            "--workers_password",
            type=str,
            help="Worker password.",
            required=False,
        )

    def _try_create_user(self, is_superuser: bool) -> None:
        if is_superuser:
            user_name = self.username_boss
            password = self.password_boss
            email = self.email_boss
        else:
            user_name = self.username_worker
            password = self.password_worker
            email = None

        if not user_name or not password:
            return

        created = create_app_user(user_name, password, is_superuser, email)

        if created:
            self.is_created = True
            self.stdout.write(self.style.SUCCESS(f"Created user {user_name}"))
        else:
            self.stdout.write(self.style.WARNING(f"User {user_name} already exists"))

    def handle(self, *args, **options):
        self.username_boss = options["boss_username"]
        self.password_boss = options["boss_password"]
        self.email_boss = options["boss_email"]
        self.username_worker = options["workers_username"]
        self.password_worker = options["workers_password"]
        self.is_created = False

        self._try_create_user(True)
        self._try_create_user(False)

        if not self.is_created:
            self.stdout.write(self.style.WARNING("No users created"))
