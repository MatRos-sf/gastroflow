__all__ = ["TableWriterSheet"]
from decimal import Decimal
from typing import Optional

from tools.spreadsheet.sheets.base import BaseSheetWriter
from tools.spreadsheet.style import CellStyle, StyleConfig


class TableWriterSheet(BaseSheetWriter):
    """Handles writing tabular data to an Excel sheet."""

    COLUMN_HEADERS = ("Name", "Quantity", "Revenue")

    def __init__(
        self,
        sheet,
        start_row: int = 1,
        start_col: int = 1,
        style_config: Optional[StyleConfig] = None,
    ):
        super().__init__(sheet, start_row, start_col, style_config)

    def write_row(self, **kwargs) -> None:
        """Write a single data row."""
        self.validate_rows(("name", "quantity", "revenue"), **kwargs)

        name = kwargs.get("name")
        quantity = kwargs.get("quantity")
        revenue = kwargs.get("revenue")

        # Use provided styles or defaults
        name_style = kwargs.get("name_style") or self._style_config.get_data_style(
            "left"
        )
        quantity_style = kwargs.get(
            "quantity_style"
        ) or self._style_config.get_data_style("center")
        revenue_style = kwargs.get(
            "revenue_style"
        ) or self._style_config.get_data_style("right")

        # Add number format to revenue
        if not revenue_style.number_format:
            revenue_style.number_format = self._style_config.FORMAT_DECIMAL

        # Name cell
        name_cell = self._sheet.cell(
            row=self._current_row, column=self._current_col, value=name
        )
        self._apply_style(name_cell, name_style)

        # Quantity cell
        quantity_cell = self._sheet.cell(
            row=self._current_row, column=self._current_col + 1, value=quantity
        )
        self._apply_style(quantity_cell, quantity_style)

        # Revenue cell
        revenue_cell = self._sheet.cell(
            row=self._current_row, column=self._current_col + 2, value=float(revenue)
        )
        self._apply_style(revenue_cell, revenue_style)

        self._current_row += 1
        self._max_name_length = max(self._max_name_length, len(name))

    def write_summary(
        self,
        total_quantity: int,
        total_revenue: Decimal,
        label: str = "Summary",
        label_style: Optional[CellStyle] = None,
        quantity_style: Optional[CellStyle] = None,
        revenue_style: Optional[CellStyle] = None,
    ) -> None:
        """Write summary row with styling."""
        # Use provided styles or defaults
        label_style = label_style or self._style_config.get_summary_style("center")
        quantity_style = quantity_style or self._style_config.get_summary_style(
            "center"
        )
        revenue_style = revenue_style or self._style_config.get_summary_style("right")

        # Add number format to revenue
        if not revenue_style.number_format:
            revenue_style.number_format = self._style_config.FORMAT_DECIMAL

        # Label cell
        summary_cell = self._sheet.cell(
            row=self._current_row, column=self._current_col, value=label
        )
        self._apply_style(summary_cell, label_style)

        # Quantity cell
        quantity_cell = self._sheet.cell(
            row=self._current_row, column=self._current_col + 1, value=total_quantity
        )
        self._apply_style(quantity_cell, quantity_style)

        # Revenue cell
        revenue_cell = self._sheet.cell(
            row=self._current_row,
            column=self._current_col + 2,
            value=float(total_revenue),
        )
        self._apply_style(revenue_cell, revenue_style)

        self._current_row += 1
