from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Generator(ABC):
    @abstractmethod
    def write_order_tables(
        self,
        items: List[Dict[str, Any]],
        additions: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        pass

    @abstractmethod
    def write_worker_stats(self, workers: Dict[str, Dict[str, Any]]) -> None:
        """Write worker stats to the spreadsheet."""
        pass

    @abstractmethod
    def write_general_stats(self, stats: Dict[str, Dict[str, Any]]) -> None:
        """Write general stats to the spreadsheet."""
        pass

    def generate_report_from_context(self, context: dict[str, Any]):
        """
        Generate a comprehensive Excel report from aggregated restaurant data.

        This method creates a multi-sheet Excel workbook containing order summaries,
        worker statistics, and general business metrics for a specified date range.

        Args:
            context: A dictionary containing aggregated restaurant data with the following structure:

                Required keys:
                    - table_report_items (QuerySet): Ordered items with fields:
                        * name_snapshot (str): Item name
                        * quantity (int): Number of items ordered
                        * line_final_total (Decimal): Total revenue for this item

                    - table_report_additions (QuerySet): Item additions/modifications with same fields
                      as table_report_items

                Optional keys:
                    - bill_summary (dict): Financial and operational summary containing:
                        * revenue (Decimal): Total revenue
                        * revenue_card (Decimal): Card payment revenue
                        * revenue_cash (Decimal): Cash payment revenue
                        * avg_per_plate (Decimal): Average revenue per plate
                        * guests (int): Total number of guests
                        * waiter (dict): Per-waiter statistics, format:
                            {
                                'waiter_name': {
                                    'bills': int,
                                    'revenue': Decimal
                                },
                                ...
                            }

                    - report (dict): Operational metrics containing:
                        * bills_status (dict): Bill status counts:
                            - opened (int): Number of open bills
                            - closed (int): Number of closed bills
                            - pay_by_card (int): Bills paid by card
                            - pay_by_cash (int): Bills paid by cash
                        * order_item_quantity (dict): Order volume by category:
                            - total (int): Total items ordered
                            - kitchen (int): Kitchen items
                            - bar (int): Bar items
                        * date_from (str): ISO 8601 formatted start date
                        * date_to (str): ISO 8601 formatted end date

                    - kitchen_metrics (dict): Kitchen performance data:
                        * avg_prep_time (timedelta): Average preparation time

        Side Effects:
            - Creates and writes data to internal Excel sheets (order tables, worker stats, general stats)
            - Saves the Excel workbook to disk using the filename specified during initialization
            - Prints success message with absolute file path upon successful save

        """
        self.write_order_tables(
            context["table_report_items"], context["table_report_additions"]
        )
        worker_stats = (
            context.get("report", {}).get("bill_summary", {}).get("waiter", {})
        )
        self.write_worker_stats(worker_stats)
        general_stats = context.get("bill_summary", {})
        general_stats.update(context.get("report", {}))
        general_stats.update(context.get("order_item_quantity", {}))
        self.write_general_stats(general_stats)
        self.save()

    @abstractmethod
    def save(self) -> None:
        """Save the spreadsheet."""
        pass


class GenerateReport:
    """Facade for generating reports using a specified generator."""

    def __init__(self, generator: Generator):
        self._generator = generator

    def generate_ordered_items(
        self,
        items: List[Dict[str, Any]],
        additions: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Generate report with ordered items and optional additions."""
        self._generator.write_order_tables(items, additions)

    def generate_worker_stats(self, stats: Dict[str, Any]) -> None:
        """Generate report with worker stats."""
        self._generator.write_worker_stats(stats)

    def generate_report_from_context(self, context: dict[str, Any]):
        self._generator.generate_report_from_context(context)

    def save(self):
        self._generator.save()
