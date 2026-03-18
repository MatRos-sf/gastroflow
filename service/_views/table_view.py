import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from tools.views.permission import BossPermissionMixin

from ..forms import HallForm
from ..models import Hall, Table


class HallListView(BossPermissionMixin, ListView):
    model = Hall
    template_name = "service/hall/list-hall.html"
    context_object_name = "halls"


class HallCreateView(BossPermissionMixin, CreateView):
    model = Hall
    form_class = HallForm
    template_name = "service/hall/create-hall.html"
    success_url = reverse_lazy("service:hall-list")

    def form_valid(self, form):
        messages.success(
            self.request,
            _("Hall '%(name)s' created.") % {"name": form.instance.name},
        )
        return super().form_valid(form)


class HallUpdateView(BossPermissionMixin, UpdateView):
    model = Hall
    form_class = HallForm
    template_name = "service/hall/update-hall.html"
    success_url = reverse_lazy("service:hall-list")

    def form_valid(self, form):
        messages.success(
            self.request,
            _("Hall '%(name)s' updated.") % {"name": form.instance.name},
        )
        return super().form_valid(form)


class HallFloorEditorView(BossPermissionMixin, DetailView):
    model = Hall
    template_name = "service/hall/floor-editor.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tables_json"] = [
            {"id": t.pk, "name": t.name, "x": t.x, "y": t.y, "size": t.size}
            for t in self.object.tables.filter(is_active=True)
        ]
        return context


@require_POST
def hall_floor_editor_save(request, pk):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return JsonResponse({"error": "forbidden"}, status=403)

    hall = get_object_or_404(Hall, pk=pk)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON"}, status=400)

    tables = data.get("tables", [])
    deleted_ids = data.get("deleted_ids", [])

    if deleted_ids:
        Table.objects.filter(pk__in=deleted_ids, hall=hall).delete()

    # Maps temp_id → real pk so JS can update data-id after save
    created = {}

    for t in tables:
        tid = t.get("id")
        temp_id = t.get("temp_id")
        name = t.get("name", "").strip() or "?"
        x = float(t.get("x", 50))
        y = float(t.get("y", 50))
        size = t.get("size", "1x1")
        if size not in ("1x1", "1x2", "1x3"):
            size = "1x1"

        if tid:
            Table.objects.filter(pk=tid, hall=hall).update(
                name=name, x=x, y=y, size=size
            )
        else:
            obj = Table.objects.create(hall=hall, name=name, x=x, y=y, size=size)
            if temp_id:
                created[temp_id] = obj.pk

    return JsonResponse({"ok": True, "created": created})
