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


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.category.name}: {self.name}"


class Addition(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    id_checkout = models.PositiveIntegerField(help_text="Cash register product ID")

    created_at = models.DateTimeField(auto_now_add=True)

    is_delete = models.BooleanField(default=False)
    priority = models.SmallIntegerField(default=1)

    class Meta:
        ordering = ["priority"]

    def __str__(self):
        return self.name


class Item(models.Model):
    """
    Represents any orderable product in the restaurant: dishes, drinks,
    desserts, packages, or any other item available on the menu.
    Items are grouped by Category (and optionally SubCategory) and routed
    to the kitchen or bar based on preparation_location.
    """

    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sub_menu = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, blank=True, null=True
    )

    preparation_location = models.CharField(
        max_length=30,
        choices=Location.choices,
        default=Location.KITCHEN,
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=100, help_text="Item name")
    description = models.TextField(
        help_text="Item description", blank=True, null=True, max_length=500
    )
    additions = models.ManyToManyField(
        Addition, blank=True, related_name="item_related"
    )
    daily_stock = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of portions available today. None = unlimited, 0 = sold out.",
    )
    id_checkout = models.PositiveIntegerField(help_text="Cash register product ID")
    price = models.DecimalField(max_digits=7, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    is_delete = models.BooleanField(default=False)

    def __str__(self):
        return self.name
