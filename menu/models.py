from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


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
    BAR = "bar", _("Bar")
    KITCHEN = "kitchen", _("Kitchen")


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("name"))

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("name"))
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, verbose_name=_("category")
    )

    class Meta:
        verbose_name = _("subcategory")
        verbose_name_plural = _("subcategories")

    def __str__(self):
        return f"{self.category.name}: {self.name}"


class Addition(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("name"))
    price = models.DecimalField(max_digits=7, decimal_places=2, verbose_name=_("price"))
    id_checkout = models.PositiveIntegerField(
        help_text=_("Cash register product ID"), verbose_name=_("checkout ID")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    is_delete = models.BooleanField(default=False, verbose_name=_("deleted"))
    priority = models.SmallIntegerField(default=1, verbose_name=_("priority"))

    class Meta:
        ordering = ["priority"]
        verbose_name = _("addition")
        verbose_name_plural = _("additions")

    def __str__(self):
        return self.name


class Item(models.Model):
    """
    Represents any orderable product in the restaurant: dishes, drinks,
    desserts, packages, or any other item available on the menu.
    Items are grouped by Category (and optionally SubCategory) and routed
    to the kitchen or bar based on preparation_location.
    """

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, verbose_name=_("category")
    )
    sub_menu = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("subcategory"),
    )
    preparation_location = models.CharField(
        max_length=30,
        choices=Location.choices,
        default=Location.KITCHEN,
        blank=True,
        null=True,
        verbose_name=_("preparation location"),
    )
    name = models.CharField(
        max_length=100, help_text=_("Item name"), verbose_name=_("name")
    )
    description = models.TextField(
        help_text=_("Item description"),
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_("description"),
    )
    additions = models.ManyToManyField(
        Addition, blank=True, related_name="item_related", verbose_name=_("additions")
    )
    daily_stock = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_(
            "Number of portions available today. None = unlimited, 0 = sold out."
        ),
        verbose_name=_("daily stock"),
    )
    id_checkout = models.PositiveIntegerField(
        help_text=_("Cash register product ID"), verbose_name=_("checkout ID")
    )
    price = models.DecimalField(max_digits=7, decimal_places=2, verbose_name=_("price"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    is_delete = models.BooleanField(default=False, verbose_name=_("deleted"))

    class Meta:
        verbose_name = _("item")
        verbose_name_plural = _("items")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("gf-menu:item-detail", kwargs={"pk": self.pk})
