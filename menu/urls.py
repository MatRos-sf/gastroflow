from django.urls import include, path

from .views import (
    AdditionCreateView,
    AdditionDetailView,
    AdditionListView,
    AdditionUpdateView,
    ItemCreateView,
    ItemDetailView,
    ItemListView,
    ItemUpdateView,
)

addition_patterns = [
    path("", AdditionListView.as_view(), name="addition-list"),
    path("add/", AdditionCreateView.as_view(), name="addition-add"),
    path("<int:pk>/", AdditionDetailView.as_view(), name="addition-detail"),
    path("<int:pk>/update/", AdditionUpdateView.as_view(), name="addition-update"),
]

urlpatterns = [
    # path("items/", ItemListView.as_view(), name="item-list"),
    path("", ItemListView.as_view(), name="item-list"),
    path("add/", ItemCreateView.as_view(), name="item-add"),
    path("<int:pk>/", ItemDetailView.as_view(), name="item-detail"),
    path("update/<int:pk>/", ItemUpdateView.as_view(), name="item-update"),
    path("addition/", include((addition_patterns, "menu"))),
]
