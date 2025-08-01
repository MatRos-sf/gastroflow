from django.db import models


class MenuType(models.TextChoices):
    MAIN = "main", "MAIN"
    MENU_FOR_CHILDREN = "menu_for_children", "MENU_FOR_CHILDREN"
    DRINK = "napoje", "NAPOJE"
    COLD_DRINK = "napoje zimne", "NAPOJE_ZIMNE"


class SubMenuType(models.TextChoices):
    COFFEE = "kawa", "KAWA"
    TEA = "herbata", "HERBATA"
    MATCHA = "matcha", "MATCHA"
    COCKTAIL = "koktajle", "KOKTAJLE"
    SOFT_DRINK = "napoje_bezalkoholowe", "NAPOJE_BEZALKOHOLOWE"


class Addition(models.Model):
    """
    Some of a dish has additional ingredient. This class allow to add it.
    """

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    is_available = models.BooleanField(default=True)


class Item(models.Model):
    menu = models.CharField(
        max_length=20,
        choices=MenuType.choices,
        default=MenuType.MAIN,
        blank=True,
        null=True,
    )
    sub_menu = models.CharField(
        max_length=30, choices=SubMenuType.choices, default=None, blank=True, null=True
    )
    name = models.CharField(max_length=100, help_text="Name of dish")
    description = models.CharField(
        help_text="Description of dish", blank=True, null=True
    )
    additions = models.ManyToManyField(
        Addition, blank=True, related_name="addition_items"
    )
    is_available = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
