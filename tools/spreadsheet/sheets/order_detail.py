__all__ = ["OrderItemSheet", "OrderAdditionSheet"]

from decimal import Decimal
from typing import Any, Optional

from tools.spreadsheet.sheets.base import BaseSheetWriter

_DECIMAL_FORMAT = "#,##0.00"


class _OrderBaseSheet(BaseSheetWriter):
    """Shared logic for order detail sheets."""

    # Subclasses must define which column indices hold decimal values.
    _DECIMAL_COLS: frozenset[int] = frozenset()
    # Subclasses must define which column index holds the item name.
    _NAME_COL: int = 0

    def _write_cells(self, values: list[Any], summary: bool = False) -> None:
        get_style = (
            self._style_config.get_summary_style
            if summary
            else self._style_config.get_data_style
        )
        for idx, value in enumerate(values):
            if idx in self._DECIMAL_COLS:
                style = get_style("right")
                style.number_format = _DECIMAL_FORMAT
                cell_value = float(value) if value is not None else ""
            elif idx == self._NAME_COL:
                style = get_style("left")
                cell_value = value or ""
            else:
                style = get_style("center")
                cell_value = value if value is not None else ""

            cell = self._sheet.cell(
                row=self._current_row,
                column=self._current_col + idx,
                value=cell_value,
            )
            self._apply_style(cell, style)

        self._current_row += 1

    def _build_title(self, date_from: Optional[str], date_to: Optional[str]) -> str:
        raise NotImplementedError

    def write_all(
        self,
        data: Any,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> None:
        self.write_headers(self._build_title(date_from, date_to))

        total_qty = 0
        total_subtotal = Decimal(0)
        total_final_total = Decimal(0)

        for row in data:
            self.write_row(row)
            total_qty += row["quantity"]
            total_subtotal += row["line_subtotal"] or Decimal(0)
            total_final_total += row.get("line_final_total") or Decimal(0)
            self._max_name_length = max(
                self._max_name_length, len(row.get("name_snapshot", ""))
            )

        self.write_summary(total_qty, total_subtotal, total_final_total)
        self._adjust_name_column()

    def write_summary(
        self,
        total_qty: int,
        total_subtotal: Decimal,
        total_final_total: Decimal,
    ) -> None:
        raise NotImplementedError

    def _adjust_name_column(self) -> None:
        """Adjust columns using defaults, but widen the name column to fit content."""
        widths = [max(len(h) + 4, 12) for h in self.COLUMN_HEADERS]
        widths[self._NAME_COL] = max(self._max_name_length + 2, widths[self._NAME_COL])
        self.adjust_columns(widths)


class OrderItemSheet(_OrderBaseSheet):
    COLUMN_HEADERS = (
        "Item PK",
        "Bill",
        "Name",
        "Qty",
        "Unit Price",
        "Subtotal",
        "Final Total",
    )
    _DECIMAL_COLS = frozenset({4, 5, 6})
    _NAME_COL = 2

    def _build_title(self, date_from: Optional[str], date_to: Optional[str]) -> str:
        if date_from and date_to:
            return f"Order Items: {date_from} – {date_to}"
        return "Order Items"

    def write_row(self, row: dict) -> None:
        self._write_cells(
            [
                row.get("pk"),
                row.get("bill_pk"),
                row.get("name_snapshot"),
                row.get("quantity"),
                row.get("price_snapshot"),
                row.get("line_subtotal"),
                row.get("line_final_total"),
            ]
        )

    def write_summary(
        self,
        total_qty: int,
        total_subtotal: Decimal,
        total_final_total: Decimal,
    ) -> None:
        # Item PK | Bill | Name      | Qty        | Unit Price | Subtotal       | Final Total
        # blank   | blank| "SUMMARY" | total_qty  | blank      | total_subtotal | total_final_total
        self._write_cells(
            [None, None, "SUMMARY", total_qty, None, total_subtotal, total_final_total],
            summary=True,
        )


class OrderAdditionSheet(_OrderBaseSheet):
    COLUMN_HEADERS = (
        "Addition PK",
        "Bill",
        "Order Item PK",
        "Name",
        "Qty",
        "Unit Price",
        "Subtotal",
        "Final Total",
    )
    _DECIMAL_COLS = frozenset({5, 6, 7})
    _NAME_COL = 3

    def _build_title(self, date_from: Optional[str], date_to: Optional[str]) -> str:
        if date_from and date_to:
            return f"Order Item Additions: {date_from} – {date_to}"
        return "Order Item Additions"

    def write_row(self, row: dict) -> None:
        self._write_cells(
            [
                row.get("pk"),
                row.get("bill_pk"),
                row.get("order_item_pk"),
                row.get("name_snapshot"),
                row.get("quantity"),
                row.get("price_snapshot"),
                row.get("line_subtotal"),
                row.get("line_final_total"),
            ]
        )

    def write_summary(
        self,
        total_qty: int,
        total_subtotal: Decimal,
        total_final_total: Decimal,
    ) -> None:
        # Addition PK | Bill | Order Item PK | Name      | Qty       | Unit Price | Subtotal       | Final Total
        # blank       | blank| blank         | "SUMMARY" | total_qty | blank      | total_subtotal | total_final
        self._write_cells(
            [
                None,
                None,
                None,
                "SUMMARY",
                total_qty,
                None,
                total_subtotal,
                total_final_total,
            ],
            summary=True,
        )
