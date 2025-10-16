from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from menu.models import Availability, Item

SAMPLE = 3


class DeliveryItemsTets(TestCase):
    def setUp(self):
        self.endpoint = reverse("delivery-product")
        for i in range(SAMPLE):
            baker.make("menu.Item", available=Availability.UNAVAILABLE)
            baker.make("menu.Item", available=Availability.SMALL_AMOUNT)

    def test_basic_check_amount_of_items(self):
        """Make sure that models has been created!"""
        self.assertEqual(Item.objects.count(), SAMPLE * 2)
        self.assertEqual(
            Item.objects.filter(available=Availability.UNAVAILABLE).count(),
            Item.objects.filter(available=Availability.SMALL_AMOUNT).count(),
        )

    def test_should_update_item_when_delivery_items_view_is_called(self):
        self.client.get(self.endpoint)
        self.assertEqual(
            Item.objects.filter(available=Availability.UNAVAILABLE).count(), 0
        )
        self.assertEqual(
            Item.objects.filter(available=Availability.SMALL_AMOUNT).count(), 0
        )

    def test_should_redirect_after_delivery_items_view_is_called(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
