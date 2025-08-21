from datetime import datetime

from django.shortcuts import render
from django.views.generic import ListView

from order.models import Location, Order


def kitchen_orders_view(request):
    return render(request, "kitchen/orders.html")


class HistoryOrderKitchen(ListView):
    model = Order
    template_name = "kitchen/history.html"
    context_object_name = "items"

    def get_queryset(self):
        # Podstawowe filtrowanie: tylko "ready"
        queryset = Order.objects.filter(status="ready", category="kitchen")

        # Sprawdzamy, czy w URL jest parametr `day` w formacie YYYY-MM-DD
        day_str = self.request.GET.get("day")
        if day_str:
            try:
                # Zamiana na obiekt daty
                selected_date = datetime.strptime(day_str, "%Y-%m-%d").date()
                queryset = queryset.filter(
                    created_at__date=selected_date  # zakładam, że masz pole `created_at`
                )
            except ValueError:
                pass  # jeśli ktoś wpisze zły format, ignorujemy
        else:
            # Domyslnie wyswietlaj dzien dzisiejszy
            today = datetime.now().date()
            queryset = queryset.filter(created_at__date=today)

        return queryset.order_by("-created_at")  # najnowsze na górze

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Lista unikalnych dni, w których były zamówienia "ready"
        context["available_days"] = Order.objects.filter(
            status="ready", category=Location.KITCHEN
        ).dates("created_at", "day", order="DESC")

        # Wybrany dzień (do podświetlenia w szablonie)
        context["selected_day"] = self.request.GET.get("day")

        return context
