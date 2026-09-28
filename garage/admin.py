from django.contrib import admin

from .models import Car, Record


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'year', 'fuel_type', 'initial_odometer', 'is_main')
    list_filter = ('fuel_type', 'is_main')
    search_fields = ('name', 'owner__email')


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('date', 'car', 'category', 'amount', 'odometer', 'quantity', 'is_full')
    list_filter = ('category',)
    search_fields = ('note', 'car__name')