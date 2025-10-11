import django_filters
from django.forms import Select

from menu.models import Location

from .models import Order


class OrderFilter(django_filters.FilterSet):
    category = django_filters.ChoiceFilter(
        choices=Location.choices,
        lookup_expr="exact",
        empty_label="Wszystkie",
        widget=Select(attrs={"class": "form-select", "onchange": "this.form.submit()"}),
        label="Wybierz lokalizacje",
    )

    class Meta:
        model = Order
        fields = ("category",)
