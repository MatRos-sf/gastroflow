import django_filters
from django import forms
from django.forms import Select
from django.utils.translation import gettext_lazy as _

from menu.models import Location
from service.models import Hall, Table

from .models import Bill, Order


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


class GroupedTableChoiceField(forms.ModelChoiceField):
    widget = forms.Select(attrs={"class": "form-select w-auto"})

    @property
    def choices(self):
        result = [("", "---------")]
        for hall in Hall.objects.prefetch_related("tables"):
            tables = [(t.pk, t.name) for t in hall.tables.all()]
            result.append((hall.name, tables))
        return result

    @choices.setter
    def choices(self, value):
        pass  # prevent Django internals from overriding our grouped choices


class BillTableFilter(django_filters.ModelChoiceFilter):
    field_class = GroupedTableChoiceField


class BillListFilter(django_filters.FilterSet):
    created_at = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control w-auto"}),
    )
    table = BillTableFilter(
        field_name="table",
        queryset=Table.objects.select_related("hall"),
    )

    class Meta:
        model = Bill
        fields = ("created_at", "table")
