from django import forms

from .models import Addition, Item


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        exclude = ("created_at",)


class AdditionForm(forms.ModelForm):
    class Meta:
        model = Addition
        exclude = ("created_at",)
