from django import forms
from django.utils.timezone import now


class DateForm(forms.Form):
    from_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Od",
        required=False,
        initial=now().date(),
    )
    to_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Do",
        required=False,
    )

    def clean_from_date(self):
        from_date = self.cleaned_data.get("from_date")
        if from_date and from_date > now().date():
            raise forms.ValidationError(
                "Data początkowa nie może być późniejsza niż dzisiaj."
            )
        return from_date

    def clean_to_date(self):
        to_date = self.cleaned_data.get("to_date")
        if to_date and to_date > now().date():
            raise forms.ValidationError(
                "Data końcowa nie może być późniejsza niż dzisiaj."
            )
        return to_date

    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get("from_date")
        to_date = cleaned_data.get("to_date")

        if from_date and to_date and from_date > to_date:
            raise forms.ValidationError(
                "Data początkowa nie może być późniejsza niż końcowa."
            )

        return cleaned_data
