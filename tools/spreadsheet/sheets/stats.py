__all__ = ["StatsSheet"]

from datetime import timedelta
from decimal import Decimal
from typing import Optional

from tools.spreadsheet.style import StyleConfig

from .base import BaseSheetWriter


class StatsSheet(BaseSheetWriter):
    COLUMN_HEADERS = ("Stats", "Value")

    def __init__(
        self,
        sheet,
        start_row: int = 1,
        start_col: int = 1,
        style_config: Optional[StyleConfig] = None,
    ):
        super().__init__(sheet, start_row, start_col, style_config)

    def write_row(self, **kwargs):
        self.validate_rows(("name", "value"), **kwargs)

        name = kwargs["name"]
        value = kwargs["value"]

        name_style, quantity_style, _ = self.get_default_style()

        # Name cell
        name_cell = self._sheet.cell(
            row=self._current_row, column=self._current_col, value=name
        )
        self._apply_style(name_cell, name_style)

        # value cell
        if isinstance(value, Decimal):
            value = f"{value:.2f}"
        elif isinstance(value, timedelta):
            total_seconds = int(value.total_seconds())

            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            value = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        value_cell = self._sheet.cell(
            row=self._current_row, column=self._current_col + 1, value=value
        )
        self._apply_style(value_cell, quantity_style)

        self._current_row += 1
        self._max_name_length = max(self._max_name_length, len(name))
