from django import forms

from .models import Addition, Item, MenuPeriod


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        exclude = ("created_at", "is_delete")
        widgets = {
            "additions": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["additions"].queryset = Addition.objects.filter(is_delete=False)


class MenuPeriodForm(forms.ModelForm):
    class Meta:
        model = MenuPeriod
        fields = ("name", "start_time", "end_time", "is_enabled", "items")
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
            "items": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["items"].queryset = (
            Item.objects.filter(is_delete=False)
            .select_related("category")
            .order_by("category__name", "name")
        )
