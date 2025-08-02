# from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Item
from .serializers import ItemSerializer


class ItemListView(APIView):
    def get(self, request):
        items = Item.objects.exclude(menu__isnull=True).exclude(menu="")
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)
