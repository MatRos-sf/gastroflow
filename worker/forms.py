from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Worker, WorkTime


class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ["first_name", "last_name", "salary", "position", "pin"]


class WorkTimeForm(forms.ModelForm):
    class Meta:
        model = WorkTime
        exclude = ("worker",)

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        finish_time = cleaned_data.get("finish_time")

        if finish_time and start_time and finish_time <= start_time:
            raise forms.ValidationError(_("Finish time must be after start time."))

        return cleaned_data
