class ValidatorError(Exception):
    """Custom validation error for invalid or missing session/bill data"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message)
        self.more_data = kwargs
        self.message = message
