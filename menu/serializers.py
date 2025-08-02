from rest_framework import serializers

from .models import Addition, Item


class AdditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Addition
        fields = ["id", "name", "price", "is_available"]


class ItemSerializer(serializers.ModelSerializer):
    additions = AdditionSerializer(many=True, read_only=True)

    class Meta:
        model = Item
        fields = [
            "id",
            "menu",
            "sub_menu",
            "name",
            "description",
            "additions",
            "is_available",
            "price",
        ]
