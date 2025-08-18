from django.contrib import admin

from .models import Bill, Notification, Order, OrderItem, OrderItemAddition

admin.site.register(Bill)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OrderItemAddition)
admin.site.register(Notification)
