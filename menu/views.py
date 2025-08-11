from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.shortcuts import get_object_or_404, redirect


from .forms import AdditionForm, ItemForm
from .models import Addition, Item

# class ItemListView(APIView):
#     def get(self, request):
#         items = Item.objects.exclude(menu__isnull=True).exclude(menu="")
#         serializer = ItemSerializer(items, many=True)
#         return Response(serializer.data)


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

    # def get_success_url(self):
    #     return reverse("item-detail", kwargs={"pk": self.object.pk})
    #


class AdditionCreateView(CreateView):
    model = Addition
    form_class = AdditionForm
    template_name = "menu/add.html"

    def get_success_url(self):
        return reverse("addition-detail", kwargs={"pk": self.object.pk})


class AdditionListView(ListView):
    model = Addition
    form_class = AdditionForm
    template_name = "menu/list.html"


class AdditionDetailView(DetailView):
    model = Addition
    template_name = "menu/detail.html"


class AdditionUpdateView(UpdateView):
    model = Addition
    form_class = AdditionForm
    template_name = "menu/add.html"

class AvailableListView(ListView):
    template_name = "menu/available_changer.html"
    model = Item

def toggle_availability(request, pk: int):
    item = get_object_or_404(Item, pk=pk)
    item.is_available = not item.is_available
    item.save()
    return redirect("available")
