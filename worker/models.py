from django.db import models


class Position(models.TextChoices):
    WAITER = "kelner", "Kelner"
    CHEF = "kucharz", "Kucharz"
    ASSISTANT = "asystent", "Asystent"
    BARISTA = "barysta", "Barysta"


class Worker(models.Model):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    salary = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    position = models.CharField(
        max_length=20, choices=Position.choices, default=Position.WAITER
    )

    def __str__(self):
        return f"{self.user.username} - {self.position}"
