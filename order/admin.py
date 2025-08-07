from django.contrib import admin

from .models import Bill, Order, OrderItem, OrderItemAddition

# Register your models here.
admin.site.register(Bill)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OrderItemAddition)
