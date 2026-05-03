from django import forms
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from order.models import Bill, StatusBill
from worker.models import Position, Worker


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


class BillEditForm(forms.ModelForm):
    pin = forms.CharField(
        max_length=4,
        required=False,
        label=_("PIN"),
        widget=forms.PasswordInput(attrs={"inputmode": "numeric", "maxlength": "4"}),
    )

    class Meta:
        model = Bill
        fields = ["waiter", "guest_count"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["waiter"].queryset = Worker.objects.filter(
            position=Position.WAITER, is_active=True
        )

    def clean(self):
        cleaned_data = super().clean()
        waiter = cleaned_data.get("waiter")
        pin = cleaned_data.get("pin")

        if waiter and waiter.pin:
            if not pin:
                raise forms.ValidationError(
                    {"pin": _("PIN is required for this waiter.")}
                )
            if pin != waiter.pin:
                raise forms.ValidationError({"pin": _("Invalid PIN.")})

        return cleaned_data


class BillCloseForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=[c for c in StatusBill.choices if c[0] != StatusBill.OPEN]
    )
    print_bill = forms.BooleanField(
        required=False, initial=False, label=_("Print bill")
    )

    class Meta:
        model = Bill
        fields = ["status", "payment_method"]


class BillDiscountForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ["discount"]
