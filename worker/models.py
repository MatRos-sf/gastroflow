from datetime import timedelta

from django.db import models
from django.utils.translation import gettext_lazy as _

from tools.models.validators import validate_digits


class Position(models.TextChoices):
    WAITER = "waiter", _("Waiter")
    CHEF = "chef", _("Chef")
    ASSISTANT = "assistant", _("Assistant")
    BARISTA = "barista", _("Barista")


class Worker(models.Model):
    first_name = models.CharField(max_length=30, verbose_name=_("first name"))
    last_name = models.CharField(max_length=30, verbose_name=_("last name"))

    salary = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0.00,
        help_text=_("per hour"),
        verbose_name=_("salary"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    position = models.CharField(
        max_length=20,
        choices=Position.choices,
        default=Position.WAITER,
        verbose_name=_("position"),
    )
    pin = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        validators=[validate_digits],
        verbose_name=_("pin"),
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class WorkTime(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True)
    start_time = models.DateTimeField()
    finish_time = models.DateTimeField()

    @property
    def duration(self) -> timedelta:
        return self.finish_time - self.start_time

    def __str__(self):
        return f"Worker: {self.duration}"
