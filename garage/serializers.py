from django.utils import timezone
from rest_framework import serializers

from .models import Car, Record


class CarSerializer(serializers.ModelSerializer):
    fuel_type_display = serializers.CharField(source='get_fuel_type_display', read_only=True)

    class Meta:
        model = Car
        fields = [
            'id', 'name', 'year', 'fuel_type', 'fuel_type_display',
            'initial_odometer', 'service_interval_km', 'is_main', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_year(self, value):
        max_year = timezone.localdate().year + 1
        if value < 1950 or value > max_year:
            raise serializers.ValidationError(f'Year must be between 1950 and {max_year}.')
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['owner'] = user
        if not user.cars.exists():
            validated_data['is_main'] = True
        if validated_data.get('is_main'):
            user.cars.update(is_main=False)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get('is_main'):
            instance.owner.cars.update(is_main=False)
        return super().update(instance, validated_data)


class RecordSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    car_name = serializers.CharField(source='car.name', read_only=True)

    class Meta:
        model = Record
        fields = [
            'id', 'car', 'car_name', 'date', 'category', 'category_display',
            'amount', 'odometer', 'quantity', 'is_full', 'note', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_car(self, value):
        if value.owner != self.context['request'].user:
            raise serializers.ValidationError('You can only use your own cars.')
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than 0.')
        return value

    def validate_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError('Date cannot be in the future.')
        return value

    def validate(self, attrs):
        category = attrs.get('category')
        quantity = attrs.get('quantity')
        if category in Record.ENERGY_CATEGORIES and (quantity is None or quantity <= 0):
            raise serializers.ValidationError(
                {'quantity': 'Quantity is required for fuel and charging records.'}
            )
        return attrs