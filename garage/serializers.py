from django.db.models import Max, Min
from django.utils import timezone
from rest_framework import serializers

from .models import Car, Record


class CarSerializer(serializers.ModelSerializer):
    fuel_type_display = serializers.CharField(source='get_fuel_type_display', read_only=True)

    class Meta:
        model = Car
        fields = (
            'id', 'name', 'year', 'fuel_type', 'fuel_type_display',
            'initial_odometer', 'service_interval_km', 'is_main', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

    # Проверка 7: год выпуска
    def validate_year(self, value):
        max_year = timezone.localdate().year + 1
        if value < 1950 or value > max_year:
            raise serializers.ValidationError(f'Year must be between 1950 and {max_year}.')
        return value

    def validate(self, attrs):
        if self.instance:
            # Проверка 9: тип машины нельзя менять, если есть записи
            new_fuel = attrs.get('fuel_type')
            if new_fuel and new_fuel != self.instance.fuel_type and self.instance.records.exists():
                raise serializers.ValidationError(
                    {'fuel_type': 'Fuel type cannot be changed because the car already has records.'}
                )
            # Проверка 10: начальный пробег не выше самого маленького пробега в записях
            new_initial = attrs.get('initial_odometer')
            if new_initial is not None:
                min_odometer = self.instance.records.aggregate(m=Min('odometer'))['m']
                if min_odometer is not None and new_initial > min_odometer:
                    raise serializers.ValidationError(
                        {'initial_odometer': f'Cannot be greater than the lowest record odometer ({min_odometer}).'}
                    )
        return attrs

    # Проверка 8: одна основная машина, первая машина становится основной
    def create(self, validated_data):
        owner = self.context['request'].user
        validated_data['owner'] = owner
        if not owner.cars.exists():
            validated_data['is_main'] = True
        car = super().create(validated_data)
        if car.is_main:
            owner.cars.exclude(pk=car.pk).update(is_main=False)
        return car

    def update(self, instance, validated_data):
        car = super().update(instance, validated_data)
        if car.is_main:
            car.owner.cars.exclude(pk=car.pk).update(is_main=False)
        return car


class RecordSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    car_name = serializers.CharField(source='car.name', read_only=True)

    # Какая энергия подходит к какому типу машины (проверка 5)
    ALLOWED_FUEL = {
        'petrol': ('petrol', 'hybrid'),
        'diesel': ('diesel',),
        'charging': ('electric',),
    }

    class Meta:
        model = Record
        fields = (
            'id', 'car', 'car_name', 'date', 'category', 'category_display',
            'amount', 'odometer', 'quantity', 'is_full', 'note', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Проверка 1: выбрать можно только свою машину
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['car'].queryset = Car.objects.filter(owner=request.user)

    # Проверка 2: машину у записи менять нельзя
    def validate_car(self, value):
        if self.instance and value != self.instance.car:
            raise serializers.ValidationError('Car cannot be changed after the record is created.')
        return value

    # Проверка 3: сумма больше нуля, дата не в будущем
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than 0.')
        return value

    def validate_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError('Date cannot be in the future.')
        return value

    def validate(self, attrs):
        # При PATCH часть полей не приходит, тогда берём их из существующей записи
        def get(field, default=None):
            if field in attrs:
                return attrs[field]
            return getattr(self.instance, field, default)

        car = get('car')
        category = get('category')
        date = get('date')
        odometer = get('odometer')
        quantity = get('quantity')

        # Проверка 4: количество только для заправки или зарядки
        if category in Record.ENERGY_CATEGORIES:
            if quantity is None or quantity <= 0:
                raise serializers.ValidationError(
                    {'quantity': 'Quantity is required for fuel/charging and must be greater than 0.'}
                )
        else:
            attrs['quantity'] = None
            attrs['is_full'] = False

        # Проверка 5: энергия соответствует типу машины
        allowed = self.ALLOWED_FUEL.get(category)
        if allowed and car.fuel_type not in allowed:
            raise serializers.ValidationError(
                {'category': f'"{category}" is not allowed for a {car.get_fuel_type_display()} car.'}
            )

        # Проверка 6: пробег не откатывается
        if odometer < car.initial_odometer:
            raise serializers.ValidationError(
                {'odometer': f'Cannot be less than the car initial odometer ({car.initial_odometer}).'}
            )
        others = car.records.all()
        if self.instance:
            others = others.exclude(pk=self.instance.pk)
        earlier_max = others.filter(date__lt=date).aggregate(m=Max('odometer'))['m']
        later_min = others.filter(date__gt=date).aggregate(m=Min('odometer'))['m']
        if earlier_max is not None and odometer < earlier_max:
            raise serializers.ValidationError(
                {'odometer': f'Cannot be less than an earlier record odometer ({earlier_max}).'}
            )
        if later_min is not None and odometer > later_min:
            raise serializers.ValidationError(
                {'odometer': f'Cannot be greater than a later record odometer ({later_min}).'}
            )

        return attrs