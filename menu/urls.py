from django.urls import path

from .views import (
    AvailableListView,
    ItemCreateView,
    ItemDetailView,
    ItemListView,
    ItemUpdateView,
    addition_quick_create,
    category_quick_create,
    delivery_items,
    subcategory_quick_create,
    toggle_availability,
)

app_name = "gf-menu"

urlpatterns = [
    # path("items/", ItemListView.as_view(), name="item-list"),
    path("item/create/", ItemCreateView.as_view(), name="item-create"),
    path("item/update/<int:pk>/", ItemUpdateView.as_view(), name="item-update"),
    path("item/<int:pk>/", ItemDetailView.as_view(), name="item-detail"),
    path("", ItemListView.as_view(), name="item-list"),
    path("add/", ItemCreateView.as_view(), name="item-add"),
    path("changer/", AvailableListView.as_view(), name="available"),
    path("toggle/<int:pk>/", toggle_availability, name="toggle-availability"),
    path("delivery-product/", delivery_items, name="delivery-product"),
    path("addition/quick-create/", addition_quick_create, name="addition-quick-create"),
    path("category/quick-create/", category_quick_create, name="category-quick-create"),
    path(
        "subcategory/quick-create/",
        subcategory_quick_create,
        name="subcategory-quick-create",
    ),
]
