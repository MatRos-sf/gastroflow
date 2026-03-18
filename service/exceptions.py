class ValidatorError(Exception):
    """Custom validation error for invalid or missing session/bill data."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message)
        self.message = message
        self.more_data = kwargs


class StockError(Exception):
    """Raised when a cart item exceeds available daily stock."""

    def __init__(self, item_name: str, available: int):
        self.item_name = item_name
        self.available = available
        super().__init__(f"{item_name}: only {available} left")
