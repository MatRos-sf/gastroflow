from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

CATEGORIES_CACHE_KEY = "menu:categories"


# TODO: remove
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


@receiver([post_save, post_delete], sender="menu.Category")
def invalidate_categories_cache(sender, **kwargs):
    cache.delete(CATEGORIES_CACHE_KEY)


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


class MenuPeriod(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    items = models.ManyToManyField(Item, blank=True)
    is_enabled = models.BooleanField(default=True)

    def get_absolute_url(self):
        return reverse("gf-menu:menu-period-detail", kwargs={"pk": self.pk})
