from datetime import timedelta

from django.db import models
from django.urls import reverse
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

    def get_absolute_url(self):
        return reverse("gf-worker:worker-detail", kwargs={"pk": self.pk})


class WorkTime(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True)
    start_time = models.DateTimeField()
    finish_time = models.DateTimeField()
    salary_snapshot = models.DecimalField(max_digits=7, decimal_places=2)

    @property
    def duration(self) -> timedelta:
        return self.finish_time - self.start_time

    @property
    def earnings(self):
        return self.duration.total_seconds() / 3600 * self.salary_snapshot

    def __str__(self):
        return f"Worker: {self.duration}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.salary_snapshot = self.worker.salary

        super().save(*args, **kwargs)
