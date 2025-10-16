from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django_filters.views import FilterView

from .filters import ItemMenuTypeFilter
from .forms import ItemForm
from .models import Availability, Item, MenuType


class ItemCreateView(CreateView):
    model = Item
    form_class = ItemForm
    template_name = "menu/add.html"
    extra_context = {"action_type": "Dodaj"}

    def get_success_url(self):
        messages.success(
            self.request, f"Pozycja została zaktualizowana: '{self.object.name}'"
        )
        return reverse("item-list")


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


class AvailableListView(FilterView):
    template_name = "menu/available_changer.html"
    model = Item
    filterset_class = ItemMenuTypeFilter
    extra_context = {
        "menu_types": [
            i[0] for i in MenuType.choices if i[0] != MenuType.UNAVAILABLE.value
        ]
    }

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.order_by("-available")


def toggle_availability(request, pk: int):
    item = get_object_or_404(Item, pk=pk)
    values = Availability.values
    current_value_idx = values.index(item.available)
    item.available = values[(current_value_idx + 1) % len(values)]
    item.save()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"available": item.available})

    return redirect("available")


def delivery_items(request):
    updated_fields = Item.objects.filter(available__gt=Availability.AVAILABLE).update(
        available=Availability.AVAILABLE
    )
    messages.success(request, f"{updated_fields} pozycji zostały przywrócone")
    return redirect("available")
