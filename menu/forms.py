from django import forms

from .models import Addition, Item


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
