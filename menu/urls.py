from django.urls import path

from .views import (
    AvailableListView,
    ItemCreateView,
    ItemDetailView,
    ItemListView,
    ItemUpdateView,
    toggle_availability,
)

urlpatterns = [
    # path("items/", ItemListView.as_view(), name="item-list"),
    path("", ItemListView.as_view(), name="item-list"),
    path("add/", ItemCreateView.as_view(), name="item-add"),
    path("<int:pk>/", ItemDetailView.as_view(), name="item-detail"),
    path("update/<int:pk>/", ItemUpdateView.as_view(), name="item-update"),
    path("changer/", AvailableListView.as_view(), name="available"),
    path("toggle/<int:pk>/", toggle_availability, name="toggle-availability"),
]
