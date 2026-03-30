from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django_filters.views import FilterView

from order.filters import BillListFilter
from order.models import Bill
from order.queries import get_bills_with_totals


class BillListView(LoginRequiredMixin, FilterView):
    template_name = "order/bill_list.html"
    paginate_by = 25
    filterset_class = BillListFilter

    def get_queryset(self) -> QuerySet[Bill]:
        return get_bills_with_totals()
