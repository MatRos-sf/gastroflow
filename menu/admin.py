from django.contrib import admin

from .models import Addition, Item

# Register your models here.

admin.site.register(Item)
admin.site.register(Addition)
