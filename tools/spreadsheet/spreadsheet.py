from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from openpyxl import Workbook

from tools.report_generator import Generator

from .sheets import StatsSheet, TableWriterSheet, WorkerStatsSheet
from .style import StyleConfig


class ManagerSpreadsheet(Generator):
    """Generates Excel spreadsheets for order reports."""

    def __init__(self, name: str, style_config: Optional[StyleConfig] = None):
        self.name = name
        self._style_config = style_config or StyleConfig()
        self._workbook = Workbook()

        # Remove default sheet and add our custom one
        if "Sheet" in self._workbook.sheetnames:
            self._workbook.remove(self._workbook["Sheet"])
        sheet_orders = self._workbook.create_sheet("tables")
        sheet_workers = self._workbook.create_sheet("workers")
        sheet_stats = self._workbook.create_sheet("stats")
        # Set default row height for better appearance
        for sheet in [sheet_orders, sheet_workers, sheet_stats]:
            sheet.sheet_properties.defaultRowHeight = 18

        self._table_sheet = TableWriterSheet(
            sheet_orders, style_config=self._style_config
        )
        self._worker_sheet = WorkerStatsSheet(
            sheet_workers, style_config=self._style_config
        )
        self._stats_sheet = StatsSheet(sheet_stats, style_config=self._style_config)

    def write_order_tables(
        self,
        items: List[Dict[str, Any]],
        additions: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Write order items and optional additions to the spreadsheet."""
        self._write_items_table("Dishes", items)

        if additions:
            self._table_sheet.start_new_table()
            self._write_items_table("Additions", additions)

    def _write_items_table(self, header_name: str, items: List[Dict[str, Any]]) -> None:
        """Write a table of items with summary."""
        self._table_sheet.write_headers(header_name)

        total_quantity = 0
        total_revenue = Decimal(0)

        for item in items:
            name = item.get("name_snapshot", "Unknown")
            quantity = item.get("quantity", 0)
            revenue = item.get("line_final_total", Decimal(0))

            self._table_sheet.write_row(name=name, quantity=quantity, revenue=revenue)
            total_quantity += quantity
            total_revenue += revenue

        self._table_sheet.write_summary(total_quantity, total_revenue)
        self._table_sheet.adjust_columns()

    def write_worker_stats(self, workers: Dict[str, Dict[str, Any]]) -> None:
        """Write worker stats to the spreadsheet."""
        self._worker_sheet.write_headers("Worker Info")
        for worker, stats in workers.items():
            bills = stats.get("bills", 0)
            revenue = stats.get("revenue", Decimal(0))
            self._worker_sheet.write_row(worker=worker, bills=bills, revenue=revenue)

        self._worker_sheet.adjust_columns()

    def __create_header_stats(self, date_from: str, date_to: str):
        if not date_from or not date_to:
            return "Stats"

        # date contains with 10 characters YYYY-MM-DD
        date_from = date_from[:10]
        date_to = date_to[:10]
        if date_from == date_to:
            return f"Stats {date_from}"
        return f"Stats {date_from} - {date_to}"

    def write_general_stats(self, stats: Dict[str, Dict[str, Any]]) -> None:
        self._stats_sheet.write_headers(
            self.__create_header_stats(
                stats.get("date_from", ""), stats.get("date_to", "")
            )
        )

        bill_status = stats.get("bills_status", {})
        self._stats_sheet.write_row(
            name="Open Bills", value=bill_status.get("opened", 0)
        )
        self._stats_sheet.write_row(
            name="Closed Bills", value=bill_status.get("closed", 0)
        )

        order_item_quantity = stats.get("order_item_quantity", {})
        sold_dishes_kitchen = order_item_quantity.get("bar", 0)
        sold_dishes_bar = order_item_quantity.get("kitchen", 0)
        sold_dishes = order_item_quantity.get("total", 0)
        self._stats_sheet.write_row(name="Sold Dishes", value=sold_dishes)
        self._stats_sheet.write_row(
            name="Sold Dishes Kitchen", value=sold_dishes_kitchen
        )
        self._stats_sheet.write_row(name="Sold Dishes Bar", value=sold_dishes_bar)

        bill_summary = stats.get("bill_summary", {})
        revenue = bill_summary.get("revenue", Decimal(0))
        revenue_card = bill_summary.get("revenue_card", Decimal(0))
        revenue_cash = bill_summary.get("revenue_cash", Decimal(0))
        avg_per_plate = bill_summary.get("avg_per_plate", Decimal(0))
        number_of_guests = bill_summary.get("guests", 0)

        self._stats_sheet.write_row(name="Revenue", value=revenue)
        self._stats_sheet.write_row(name="Revenue Card", value=revenue_card)
        self._stats_sheet.write_row(name="Revenue Cash", value=revenue_cash)
        self._stats_sheet.write_row(
            name="Average revenue per plate", value=avg_per_plate
        )
        self._stats_sheet.write_row(name="Number of guests", value=number_of_guests)

        self._stats_sheet.write_row(
            name="Average time to prepare a dish",
            value=stats.get("kitchen_metrics", {}).get("avg_prep_time", 0),
        )
        self._stats_sheet.adjust_columns()

    def save(self) -> None:
        """Save the workbook to file."""
        import os

        try:
            # Ensure directory exists
            directory = os.path.dirname(self.name)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            self._workbook.save(self.name)
            print(f"File saved successfully: {os.path.abspath(self.name)}")
        except PermissionError:
            print(f"Permission denied: Cannot write to {self.name}")
        except Exception as e:
            print(f"Error saving file: {e}")

    @staticmethod
    def create_report_name(
        from_date: datetime, to_date: Optional[datetime] = None
    ) -> str:
        """Generate a report filename based on date range."""
        if to_date and to_date.date() != from_date.date():
            return f"raport_{from_date.date()}_{to_date.date()}.xlsx"
        return f"raport_{from_date.date()}.xlsx"
