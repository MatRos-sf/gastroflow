from django.db.models import QuerySet
from django.utils import timezone
from django.views.generic import ListView

from menu.models import Category, Item, MenuPeriod, SubCategory


class MenuWaiterView(ListView):
    model = Item
    template_name = "service/order_flow/items_waiter.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self._active_period = self._resolve_active_period()

    def _resolve_active_period(self) -> MenuPeriod | None:
        period_pk = self.request.session.get("menu_period")
        if period_pk:
            try:
                return MenuPeriod.objects.get(pk=period_pk, is_enabled=True)
            except MenuPeriod.DoesNotExist:
                del self.request.session["menu_period"]
        now = timezone.localtime().time()
        return MenuPeriod.objects.filter(
            is_enabled=True, start_time__lte=now, end_time__gte=now
        ).first()

    def _get_category(self) -> Category | None:
        try:
            pk = int(self.request.GET.get("category", 0))
            return Category.objects.get(pk=pk)
        except (ValueError, Category.DoesNotExist):
            return Category.objects.first()

    def get_queryset(self):
        category = self._get_category()
        if category is None:
            return Item.objects.none()
        qs = Item.objects.filter(category=category, is_delete=False)
        if self._active_period is not None:
            qs = qs.filter(pk__in=self._active_period.items.all())
        return qs.select_related("sub_menu").prefetch_related("additions")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_category"] = self._get_category()
        available_items = Item.objects.filter(is_delete=False)
        if self._active_period is not None:
            available_items = available_items.filter(
                pk__in=self._active_period.items.all()
            )
        context["categories"] = Category.objects.filter(
            item__in=available_items
        ).distinct()
        context["active_period"] = self._active_period
        context["all_periods"] = MenuPeriod.objects.filter(is_enabled=True)

        qs = context["object_list"]
        items_no_sub = qs.filter(sub_menu__isnull=True)
        items_with_sub = qs.exclude(sub_menu__isnull=True).order_by("sub_menu__name")

        sub_menu_groups: dict[SubCategory, QuerySet] = {}
        for sub in SubCategory.objects.filter(item__in=items_with_sub).distinct():
            sub_menu_groups[sub] = items_with_sub.filter(sub_menu=sub)

        context["items_no_sub"] = items_no_sub
        context["sub_menu_groups"] = sub_menu_groups

        return context
