from django_filters import ChoiceFilter, FilterSet

from .models import Item, MenuType


class ItemMenuTypeFilter(FilterSet):
    menu = ChoiceFilter(choices=MenuType.choices)

    class Meta:
        model = Item
        fields = ("menu",)
