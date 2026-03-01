from django.db import models
from django.utils.translation import gettext_lazy as _


class Position(models.TextChoices):
    WAITER = "waiter", _("Waiter")
    CHEF = "chef", _("Chef")
    ASSISTANT = "assistant", _("Asystent")
    BARISTA = "barista", _("Barista")


class Worker(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    salary = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    position = models.CharField(
        max_length=20, choices=Position.choices, default=Position.WAITER
    )
    pin = models.SmallIntegerField(max_length=4, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} - {self.last_name}"
