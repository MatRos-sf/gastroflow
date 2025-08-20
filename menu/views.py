from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import ItemForm
from .models import Item, MenuType


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

    def get_queryset(self):
        category = self.request.GET.get("category", MenuType.MAIN)
        return Item.objects.filter(menu=category).order_by("id_checkout")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = [(value, label) for value, label in MenuType.choices]
        context["selected_category"] = self.request.GET.get("category", MenuType.MAIN)
        return context


class ItemDetailView(DetailView):
    model = Item
    template_name = "menu/detail.html"


class ItemUpdateView(UpdateView):
    model = Item
    form_class = ItemForm
    template_name = "menu/add.html"
    extra_context = {"action_type": "Edytuj"}

    def get_success_url(self):
        messages.success(
            self.request, f"Pozycja została zaktualizowana: '{self.object.name}'"
        )
        return reverse("item-list")


class AvailableListView(ListView):
    template_name = "menu/available_changer.html"
    model = Item


def toggle_availability(request, pk: int):
    item = get_object_or_404(Item, pk=pk)
    item.is_available = not item.is_available
    item.save()
    return redirect("available")
