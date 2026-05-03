from django.core.exceptions import ValidationError


def validate_digits(value):
    if not value.isdigit():
        raise ValidationError("PIN must be a number.")
