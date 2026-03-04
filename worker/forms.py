from django import forms

from .models import Worker, WorkTime


class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ["first_name", "last_name", "salary", "position", "pin"]


class WorkTimeForm(forms.ModelForm):
    class Meta:
        model = WorkTime
        exclude = ("worker",)
