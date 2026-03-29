import django_filters
from django.forms import Select
from django.utils.translation import gettext_lazy as _

from menu.models import Location

from .models import Order


class OrderFilter(django_filters.FilterSet):
    category = django_filters.ChoiceFilter(
        choices=Location.choices,
        lookup_expr="exact",
        empty_label=_("All"),
        widget=Select(attrs={"class": "form-select", "onchange": "this.form.submit()"}),
        label=_("Choose localization"),
    )

    class Meta:
        model = Order
        fields = ("category",)
