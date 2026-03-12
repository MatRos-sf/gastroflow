from django.urls import path

from .views import (
    ItemCreateView,
    ItemDailyStockListView,
    ItemDetailView,
    ItemListView,
    ItemReplenishView,
    ItemUpdateView,
    addition_quick_create,
    category_quick_create,
    set_daily_stock,
    subcategory_quick_create,
    supply_all_items,
    supply_item,
)

app_name = "gf-menu"

urlpatterns = [
    path("item/", ItemListView.as_view(), name="item-list"),
    path("item/create/", ItemCreateView.as_view(), name="item-create"),
    path("item/update/<int:pk>/", ItemUpdateView.as_view(), name="item-update"),
    path("item/<int:pk>/", ItemDetailView.as_view(), name="item-detail"),
    path(
        "item/daily-stock/", ItemDailyStockListView.as_view(), name="item-daily-stock"
    ),
    path("item/replenish/", ItemReplenishView.as_view(), name="item-replenish"),
    path("item/<int:pk>/set-stock/", set_daily_stock, name="item-set-stock"),
    path("item/<int:pk>/supply/", supply_item, name="item-supply"),
    path("item/supply-all/", supply_all_items, name="item-supply-all"),
    path("addition/quick-create/", addition_quick_create, name="addition-quick-create"),
    path("category/quick-create/", category_quick_create, name="category-quick-create"),
    path(
        "subcategory/quick-create/",
        subcategory_quick_create,
        name="subcategory-quick-create",
    ),
]
