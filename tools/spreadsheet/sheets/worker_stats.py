__all__ = ["WorkerStatsSheet"]
from typing import Optional

from tools.spreadsheet.sheets.base import BaseSheetWriter
from tools.spreadsheet.style import StyleConfig


class WorkerStatsSheet(BaseSheetWriter):
    """Handles writing tabular data to an Excel sheet."""

    COLUMN_HEADERS = ("Name", "Bills", "Revenue")

    def __init__(
        self,
        sheet,
        start_row: int = 1,
        start_col: int = 1,
        style_config: Optional[StyleConfig] = None,
    ):
        super().__init__(sheet, start_row, start_col, style_config)

    def write_row(self, **kwargs):
        name = kwargs.get("worker")
        bills = kwargs.get("bills")
        revenue = kwargs.get("revenue")

        name_style = kwargs.get("name_style") or self._style_config.get_data_style(
            "left"
        )
        bills_style = kwargs.get("bills_style") or self._style_config.get_data_style(
            "center"
        )
        revenue_style = kwargs.get(
            "revenue_style"
        ) or self._style_config.get_data_style("right")

        # Add number format to revenue
        if not revenue_style.number_format:
            revenue_style.number_format = self._style_config.FORMAT_DECIMAL

        name_cell = self._sheet.cell(
            row=self._current_row, column=self._start_col, value=name
        )
        self._apply_style(name_cell, name_style)

        bills_cell = self._sheet.cell(
            row=self._current_row, column=self._start_col + 1, value=bills
        )
        self._apply_style(bills_cell, bills_style)

        revenue_cell = self._sheet.cell(
            row=self._current_row, column=self._start_col + 2, value=revenue
        )
        self._apply_style(revenue_cell, revenue_style)

        self._current_row += 1
        self._max_name_length = max(self._max_name_length, len(name))
