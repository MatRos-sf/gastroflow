from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import ItemForm
from .models import Item


class ItemCreateView(CreateView):
    model = Item
    form_class = ItemForm
    template_name = "menu/add.html"

    def get_success_url(self):
        return reverse("item-detail", kwargs={"pk": self.object.pk})


class ItemListView(ListView):
    model = Item
    form_class = ItemForm
    template_name = "menu/list.html"


class ItemDetailView(DetailView):
    model = Item
    template_name = "menu/detail.html"


class ItemUpdateView(UpdateView):
    model = Item
    form_class = ItemForm
    template_name = "menu/add.html"


class AvailableListView(ListView):
    template_name = "menu/available_changer.html"
    model = Item


def toggle_availability(request, pk: int):
    item = get_object_or_404(Item, pk=pk)
    item.is_available = not item.is_available
    item.save()
    return redirect("available")
