from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django_filters.views import FilterView

from .filters import ItemMenuTypeFilter
from .forms import ItemForm
from .models import Addition, Availability, Category, Item, MenuType, SubCategory


class ItemCreateView(CreateView):
    model = Item
    form_class = ItemForm
    template_name = "menu/create-item.html"

    def get_success_url(self):
        return reverse("gf-menu:item-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(
            self.request, _("Item added: '%(name)s'") % {"name": self.object.name}
        )
        return super().form_valid(form)


class ItemUpdateView(UpdateView):
    model = Item
    form_class = ItemForm
    template_name = "menu/update-item.html"

    def get_success_url(self):
        return reverse("gf-menu:item-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(
            self.request,
            _("Item '%(name)s' has been updated.") % {"name": self.object.name},
        )
        return super().form_valid(form)


class ItemDetailView(DetailView):
    model = Item
    template_name = "menu/detail-item.html"


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


def addition_quick_create(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        price = request.POST.get("price", "0")
        id_checkout = request.POST.get("id_checkout", "0")
        priority = request.POST.get("priority", "1")
        if name:
            addition = Addition.objects.create(
                name=name, price=price, id_checkout=id_checkout, priority=priority
            )
            return JsonResponse({"id": addition.pk, "name": addition.name})
    return JsonResponse({"error": "invalid"}, status=400)


def category_quick_create(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            category = Category.objects.create(name=name)
            return JsonResponse({"id": category.pk, "name": category.name})
    return JsonResponse({"error": "invalid"}, status=400)


def subcategory_quick_create(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        category_id = request.POST.get("category_id", "").strip()
        if name and category_id:
            category = get_object_or_404(Category, pk=category_id)
            subcategory = SubCategory.objects.create(name=name, category=category)
            return JsonResponse({"id": subcategory.pk, "name": subcategory.name})
    return JsonResponse({"error": "invalid"}, status=400)


def delivery_items(request):
    updated_fields = Item.objects.filter(available__gt=Availability.AVAILABLE).update(
        available=Availability.AVAILABLE
    )
    messages.success(request, f"{updated_fields} pozycji zostały przywrócone")
    return redirect("available")
