from django.conf import settings
from django.db import models


class Car(models.Model):
    class FuelType(models.TextChoices):
        PETROL = 'petrol', 'Petrol'
        DIESEL = 'diesel', 'Diesel'
        HYBRID = 'hybrid', 'Hybrid'
        ELECTRIC = 'electric', 'Electric'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cars')
    name = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField()
    fuel_type = models.CharField(max_length=10, choices=FuelType.choices)
    initial_odometer = models.PositiveIntegerField()
    service_interval_km = models.PositiveIntegerField(default=10000)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_main', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.year})"


class Record(models.Model):
    class Category(models.TextChoices):
        PETROL = 'petrol', 'Petrol'
        DIESEL = 'diesel', 'Diesel'
        CHARGING = 'charging', 'Charging'
        SERVICE = 'service', 'Service'
        REPAIR = 'repair', 'Repair'
        INSURANCE = 'insurance', 'Insurance'
        PARKING = 'parking', 'Parking'
        WASH = 'wash', 'Wash'
        OTHER = 'other', 'Other'


    ENERGY_CATEGORIES = ('petrol', 'diesel', 'charging')

    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='records')
    date = models.DateField()
    category = models.CharField(max_length=20, choices=Category.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    odometer = models.PositiveIntegerField()
    quantity = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    is_full = models.BooleanField(default=False)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-odometer']

    def __str__(self):
        return f"{self.date} {self.get_category_display()} {self.amount} GEL"