from django import forms

from .models import Item, MenuType


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        exclude = ("created_at",)
        widgets = {
            "additions": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["additions"].queryset = Item.objects.filter(menu=MenuType.OTHER)
