from abc import ABC, abstractmethod
from typing import Optional, Tuple

from openpyxl.utils import get_column_letter

from tools.spreadsheet.style import CellStyle, StyleConfig


class BaseSheetWriter(ABC):
    """Abstract base class for writing tabular data to Excel sheets."""

    # Subclasses must define their column headers
    COLUMN_HEADERS: Tuple[str, ...] = ()

    def __init__(
        self,
        sheet,
        start_row: int = 1,
        start_col: int = 1,
        style_config: Optional[StyleConfig] = None,
    ):
        self._sheet = sheet
        self._start_row = start_row
        self._start_col = start_col
        self._current_row = start_row
        self._current_col = start_col
        self._max_name_length = 0
        self._style_config = style_config or StyleConfig()

    def _apply_style(self, cell, style: CellStyle) -> None:
        """Apply a CellStyle to a cell."""
        if style.font:
            cell.font = style.font
        if style.fill:
            cell.fill = style.fill
        if style.alignment:
            cell.alignment = style.alignment
        if style.border:
            cell.border = style.border
        if style.number_format:
            cell.number_format = style.number_format

    def write_headers(
        self,
        main_title: str,
        title_style: Optional[CellStyle] = None,
        header_style: Optional[CellStyle] = None,
    ) -> None:
        """Write column headers to the sheet."""
        # Use provided styles or defaults
        title_style = title_style or self._style_config.get_title_style()
        header_style = header_style or self._style_config.get_header_style()

        # Write main title (merged across 3 columns)
        cell = self._sheet.cell(row=self._current_row, column=self._current_col)
        cell.value = main_title
        self._apply_style(cell, title_style)

        # Merge cells for title
        self._sheet.merge_cells(
            start_row=self._current_row,
            start_column=self._current_col,
            end_row=self._current_row,
            end_column=self._current_col + 2,
        )
        self._current_row += 1

        # Write column headers
        for idx, header in enumerate(self.COLUMN_HEADERS):
            cell = self._sheet.cell(
                row=self._current_row, column=self._current_col + idx
            )
            cell.value = header
            self._apply_style(cell, header_style)
        self._current_row += 1

    def validate_rows(self, expected_kwargs: tuple[str, ...], **kwargs) -> None:
        """Extract and validate required kwargs"""
        missing = [key for key in expected_kwargs if key not in kwargs]
        if missing:
            raise ValueError(f"Missing required kwargs: {missing}")

    @abstractmethod
    def write_row(self, **kwargs) -> None:
        pass

    def adjust_columns(
        self,
        name_width: Optional[int] = None,
        quantity_width: int = 12,
        revenue_width: int = 15,
    ) -> None:
        """Adjust column widths based on content."""
        # Name column - based on content or provided width
        col_letter = get_column_letter(self._current_col)
        width = name_width or max(self._max_name_length + 2, 20)
        self._sheet.column_dimensions[col_letter].width = width

        # Quantity column
        col_letter = get_column_letter(self._current_col + 1)
        self._sheet.column_dimensions[col_letter].width = quantity_width

        # Revenue column
        col_letter = get_column_letter(self._current_col + 2)
        self._sheet.column_dimensions[col_letter].width = revenue_width

    def start_new_table(self, column_gap: int = 2) -> None:
        """Start a new table with specified offset from current position."""
        self._current_row = self._start_row
        self._current_col += len(self.COLUMN_HEADERS) + column_gap
        self._max_name_length = 0
