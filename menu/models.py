from django.db import models


class MenuType(models.TextChoices):
    MAIN = "menu", "Menu"
    MENU_FOR_CHILDREN = "menu dla dzieci", "Menu dla dzieci"
    DRINK = "napoje", "Napoje"
    COLD_DRINK = "zimne napoje", "Zimne napoje"
    DESSERT = "deser", "Deser"
    OTHER = "inne", "Inne"
    UNAVAILABLE = "niedostępny", "Niedostępny"


class SubMenuType(models.TextChoices):
    COFFEE = "kawa", "Kawa"
    TEA = "herbata", "Herbata"
    MATCHA = "matcha", "Matcha"
    COCKTAIL = "koktajle", "Koktajle"
    SOFT_DRINK = "pitku", "Pitku"
    WAFFLE = "gofry", "Gofry"
    CAKE = "ciasto", "Ciasto"


class Availability(models.IntegerChoices):
    AVAILABLE = 1, "Available"
    SMALL_AMOUNT = 2, "Small amount"
    UNAVAILABLE = 3, "Unavailable"


class Location(models.TextChoices):
    BAR = "bar", "BAR"
    KITCHEN = "kitchen", "KITCHEN"


class Item(models.Model):
    menu = models.CharField(
        max_length=20,
        choices=MenuType.choices,
        default=MenuType.MAIN,
        blank=True,
        null=True,
    )
    sub_menu = models.CharField(
        max_length=20,
        choices=SubMenuType.choices,
        default=None,
        blank=True,
        null=True,
    )

    preparation_location = models.CharField(
        max_length=30,
        choices=Location.choices,
        default=Location.KITCHEN,
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=100, help_text="Name of dish")
    description = models.CharField(
        help_text="Description of dish", blank=True, null=True
    )
    additions = models.ManyToManyField(
        "self", blank=True, symmetrical=False, related_name="is_addition_to"
    )
    available = models.SmallIntegerField(
        choices=Availability.choices, default=Availability.AVAILABLE
    )
    id_checkout = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
