from django import forms

from .models import Worker


class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ["first_name", "last_name", "salary", "position", "pin"]
