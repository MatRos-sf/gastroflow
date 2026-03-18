from django.db.models import Prefetch
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from service.models import Hall, Table

def table_select_view(request):
    if request.method == "GET":
        halls = Hall.objects.filter(is_active=True).prefetch_related(
            Prefetch("tables", queryset=Table.objects.filter(is_active=True))
        )
        return render(request, "service/order_flow/table_order.html", {"halls": halls})

    elif request.method == "POST":
        tables_selected = request.POST.get("tables")
        if not tables_selected:
            messages.error(request, _("Select a table to proceed to the order"))
            return redirect("service:order-select-table")
        tables_list = [int(t.strip()) for t in tables_selected.split(",")]
        request.session["tables"] = tables_list
        return redirect("service:order-select-items")