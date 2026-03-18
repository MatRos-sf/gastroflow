from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Hall


class HallForm(forms.ModelForm):
    class Meta:
        model = Hall
        fields = ("name", "order", "aspect_w", "aspect_h", "is_active")
        labels = {
            "aspect_w": _("Aspect ratio — width"),
            "aspect_h": _("Aspect ratio — height"),
        }
        help_texts = {
            "aspect_w": _("e.g. 2 for a 2:1 (wide) room"),
            "aspect_h": _("e.g. 1 for a 2:1 (wide) room"),
        }
