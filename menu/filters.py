from django.core.cache import cache
from django_filters import ChoiceFilter, FilterSet, ModelChoiceFilter

from .models import CATEGORIES_CACHE_KEY, Category, Item, Location


def _get_categories(request):
    result = cache.get(CATEGORIES_CACHE_KEY)
    if result is None:
        result = Category.objects.all()
        cache.set(CATEGORIES_CACHE_KEY, result, timeout=600)
    return result


class ItemListFilter(FilterSet):
    category = ModelChoiceFilter(
        queryset=_get_categories,
        empty_label=None,
        required=False,
    )
    preparation_location = ChoiceFilter(
        choices=[("", "-")] + list(Location.choices),
        empty_label=None,
    )

    class Meta:
        model = Item
        fields = ("category", "preparation_location")
