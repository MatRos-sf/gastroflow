from django.db import models


class MenuType(models.TextChoices):
    MAIN = "main", "Main menu"
    MENU_FOR_CHILDREN = "menu_for_children", "Menu for children"
    DRINK = "drinks", "Drinks"
    COLD_DRINK = "cold_drinks", "Cold drinks"


class CategoryOrder(models.TextChoices):
    BAR = "bar", "BAR"
    KITCHEN = "kitchen", "KITCHEN"


class Addition(models.Model):
    """
    Some of a dish has additional ingredient. This class allow to add it.
    """

    name = models.CharField(max_length=100)
    id_checkout = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Item(models.Model):
    menu = models.CharField(
        max_length=20,
        choices=MenuType.choices,
        default=MenuType.MAIN,
        blank=True,
        null=True,
    )
    category = models.CharField(
        max_length=30, choices=CategoryOrder.choices, default=None, blank=True, null=True
    )
    name = models.CharField(max_length=100, help_text="Name of dish")
    description = models.CharField(
        help_text="Description of dish", blank=True, null=True
    )
    additions = models.ManyToManyField(
        Addition, blank=True, related_name="addition_items"
    )
    is_available = models.BooleanField(default=True)
    id_checkout = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
