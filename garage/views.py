from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, filters
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Max, Sum

from .models import Car, Record
from .serializers import CarSerializer, RecordSerializer


def get_date_param(request, name):
    """Читает дату из адреса (?date_from=2026-09-01). Неверная дата -> 400, а не 500."""
    value = request.query_params.get(name)
    if not value:
        return None
    try:
        parsed = parse_date(value)
    except ValueError:
        parsed = None
    if parsed is None:
        raise ValidationError({name: 'Invalid date. Use format YYYY-MM-DD.'})
    return parsed


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CarListCreateView(generics.ListCreateAPIView):
    serializer_class = CarSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Car.objects.none()
        return Car.objects.filter(owner=self.request.user)


class CarDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CarSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Car.objects.none()
        return Car.objects.filter(owner=self.request.user)

    def perform_destroy(self, instance):
        was_main = instance.is_main
        owner = instance.owner
        instance.delete()
        # Если удалили основную машину, основной становится самая новая из оставшихся
        if was_main:
            next_car = owner.cars.order_by('-created_at').first()
            if next_car:
                next_car.is_main = True
                next_car.save(update_fields=['is_main'])


class CarSetMainView(APIView):
    @extend_schema(request=None, responses=CarSerializer)
    def post(self, request, pk):
        car = get_object_or_404(Car, pk=pk, owner=request.user)
        Car.objects.filter(owner=request.user).update(is_main=False)
        car.is_main = True
        car.save(update_fields=['is_main'])
        return Response(CarSerializer(car, context={'request': request}).data)


class RecordListCreateView(generics.ListCreateAPIView):
    serializer_class = RecordSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['note']
    ordering_fields = ['date', 'amount', 'odometer']

    @extend_schema(parameters=[
        OpenApiParameter('car', OpenApiTypes.INT, description='Car id'),
        OpenApiParameter('category', OpenApiTypes.STR, enum=Record.Category.values),
        OpenApiParameter('date_from', OpenApiTypes.DATE, description='From date (YYYY-MM-DD)'),
        OpenApiParameter('date_to', OpenApiTypes.DATE, description='To date (YYYY-MM-DD)'),
    ])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Record.objects.none()
        queryset = Record.objects.filter(car__owner=self.request.user).select_related('car')

        car = self.request.query_params.get('car')
        category = self.request.query_params.get('category')
        date_from = get_date_param(self.request, 'date_from')
        date_to = get_date_param(self.request, 'date_to')

        if car:
            if not car.isdigit():
                raise ValidationError({'car': 'Car must be a number.'})
            queryset = queryset.filter(car_id=car)
        if category:
            queryset = queryset.filter(category=category)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        return queryset


class RecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RecordSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Record.objects.none()
        return Record.objects.filter(car__owner=self.request.user).select_related('car')

class CarStatsView(APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, pk):
        car = get_object_or_404(Car, pk=pk, owner=request.user)
        records = car.records.all()

        total_spent = records.aggregate(total=Sum('amount'))['total'] or 0

        by_category = {}
        for row in records.values('category').annotate(total=Sum('amount')):
            by_category[row['category']] = row['total']

        current_odometer = records.aggregate(m=Max('odometer'))['m'] or car.initial_odometer

        return Response({
            'car': car.name,
            'current_odometer': current_odometer,
            'total_spent': total_spent,
            'by_category': by_category,
        })