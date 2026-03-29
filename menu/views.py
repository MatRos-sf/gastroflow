from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django_filters.views import FilterView

from tools.views.permission import BossPermissionMixin

from .filters import ItemListFilter
from .forms import ItemForm, MenuPeriodForm
from .models import Addition, Category, Item, MenuPeriod, SubCategory


class ItemCreateView(BossPermissionMixin, CreateView):
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


class ItemUpdateView(BossPermissionMixin, UpdateView):
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


class ItemDetailView(BossPermissionMixin, DetailView):
    model = Item
    template_name = "menu/detail-item.html"


class ItemBaseListView(FilterView):
    model = Item
    filterset_class = ItemListFilter
    paginate_by = 50

    def get_queryset(self):
        return (
            Item.objects.select_related("category", "sub_menu")
            .prefetch_related("additions")
            .order_by("id_checkout")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context["filter_params"] = params.urlencode()
        return context


class ItemListView(BossPermissionMixin, ItemBaseListView):
    """Full menu item list. Boss only."""

    template_name = "menu/list-item.html"


class ItemDailyStockListView(LoginRequiredMixin, ItemBaseListView):
    """Manage which items have daily stock tracking enabled. Boss only."""

    template_name = "menu/daily-stock-item.html"


class ItemReplenishView(LoginRequiredMixin, ItemBaseListView):
    """Morning replenish view — shows only tracked items so staff can set today's portions."""

    template_name = "menu/replenish-item.html"

    def get_queryset(self):
        return super().get_queryset().filter(daily_stock__isnull=False)


@login_required
def set_daily_stock(request, pk: int):
    if request.method == "POST":
        item = get_object_or_404(Item, pk=pk)
        value = request.POST.get("daily_stock", "").strip()
        item.daily_stock = int(value) if value != "" else None
        item.save(update_fields=["daily_stock"])
        messages.success(request, _("Set daily stock for '%(name)s'") % {"name": item})
    return redirect("gf-menu:item-daily-stock")


@user_passes_test(lambda u: u.is_superuser)
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


@user_passes_test(lambda u: u.is_superuser)
def category_quick_create(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            category = Category.objects.create(name=name)
            return JsonResponse({"id": category.pk, "name": category.name})
    return JsonResponse({"error": "invalid"}, status=400)


@user_passes_test(lambda u: u.is_superuser)
def subcategory_quick_create(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        category_id = request.POST.get("category_id", "").strip()
        if name and category_id:
            category = get_object_or_404(Category, pk=category_id)
            subcategory = SubCategory.objects.create(name=name, category=category)
            return JsonResponse({"id": subcategory.pk, "name": subcategory.name})
    return JsonResponse({"error": "invalid"}, status=400)


@login_required
def supply_item(request, pk: int):
    if request.method == "POST":
        item = get_object_or_404(Item, pk=pk)
        item.daily_stock = None
        item.save(update_fields=["daily_stock"])
        messages.success(request, _("Supplied '%(name)s'") % {"name": item})
    return redirect("gf-menu:item-replenish")


@login_required
def supply_all_items(request):
    if request.method == "POST":
        updated = Item.objects.filter(
            daily_stock__isnull=False, is_delete=False
        ).update(daily_stock=None)
        messages.success(request, _("Supplied %(count)s items") % {"count": updated})
    return redirect("gf-menu:item-replenish")


class MenuPeriodFormMixin:
    model = MenuPeriod
    form_class = MenuPeriodForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.prefetch_related(
            Prefetch(
                "item_set",
                queryset=Item.objects.filter(is_delete=False).order_by("name"),
            )
        ).order_by("name")
        obj = getattr(self, "object", None)
        context["selected_item_pks"] = (
            set(obj.items.values_list("pk", flat=True)) if obj and obj.pk else set()
        )
        return context


class MenuPeriodCreateView(BossPermissionMixin, MenuPeriodFormMixin, CreateView):
    template_name = "menu/create-menu-period.html"

    def form_valid(self, form):
        messages.success(
            self.request,
            _("Menu period '%(name)s' created.") % {"name": form.instance.name},
        )
        return super().form_valid(form)


class MenuPeriodUpdateView(BossPermissionMixin, MenuPeriodFormMixin, UpdateView):
    template_name = "menu/update-menu-period.html"

    def form_valid(self, form):
        messages.success(
            self.request,
            _("Menu period '%(name)s' updated.") % {"name": form.instance.name},
        )
        return super().form_valid(form)


class MenuPeriodDetailView(BossPermissionMixin, DetailView):
    model = MenuPeriod
    template_name = "menu/detail-menu-period.html"


class MenuDashboardView(BossPermissionMixin, TemplateView):
    template_name = "menu/dashboard.html"


class MenuPeriodListView(BossPermissionMixin, ListView):
    model = MenuPeriod
    template_name = "menu/list-menu-period.html"
    queryset = MenuPeriod.objects.order_by("-is_enabled", "name")
