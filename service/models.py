from django.db import models
from django.utils.translation import gettext_lazy as _


class TableSize(models.TextChoices):
    ONE_BY_ONE = "1x1", _("1×1")
    ONE_BY_TWO = "1x2", _("1×2")
    ONE_BY_THREE = "1x3", _("1×3")


class Hall(models.Model):
    name = models.CharField(max_length=50)
    order = models.PositiveSmallIntegerField(default=0)
    aspect_w = models.PositiveSmallIntegerField(default=2)  # CSS aspect-ratio numerator
    aspect_h = models.PositiveSmallIntegerField(
        default=1
    )  # CSS aspect-ratio denominator
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Table(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name="tables")
    name = models.CharField(max_length=10)
    x = models.FloatField()  # 0.0–100.0, % of canvas width
    y = models.FloatField()  # 0.0–100.0, % of canvas height
    size = models.CharField(
        max_length=3, choices=TableSize.choices, default=TableSize.ONE_BY_ONE
    )
    is_active = models.BooleanField(default=True)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return self.name
