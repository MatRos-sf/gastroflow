from django.core.exceptions import ValidationError
from django.test import TestCase
from parameterized import parameterized

from tools.models.validators import validate_digits


class ValidateDigitsTest(TestCase):
    @parameterized.expand(
        [
            ("1234",),
            ("0000",),
            ("1234",),
        ]
    )
    def test_validates_digits(self, value):
        self.assertIsNone(validate_digits(value))

    @parameterized.expand(
        [
            ("123a",),
            ("-123",),
            ("",),
        ]
    )
    def test_raises_validation_error(self, value):
        with self.assertRaises(ValidationError):
            validate_digits(value)
