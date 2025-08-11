from django.db import models


# Create your models here.
class Table(models.Model):
    name = models.CharField(max_length=10)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()
    btn_type = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
