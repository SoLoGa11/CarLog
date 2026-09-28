from django.db.models import Max, Sum
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Car, Record
from .serializers import CarSerializer, RecordSerializer


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


class CarSetMainView(APIView):
    @extend_schema(request=None, responses=CarSerializer)
    def post(self, request, pk):
        car = get_object_or_404(Car, pk=pk, owner=request.user)
        Car.objects.filter(owner=request.user).update(is_main=False)
        car.is_main = True
        car.save()
        return Response(CarSerializer(car).data)


class CarStatsView(APIView):
    @extend_schema(responses=dict)
    def get(self, request, pk):
        car = get_object_or_404(Car, pk=pk, owner=request.user)
        records = car.records.all()

        total_spent = records.aggregate(total=Sum('amount'))['total'] or 0

        by_category = {}
        for row in records.values('category').annotate(total=Sum('amount')):
            by_category[row['category']] = row['total']

        max_odometer = records.aggregate(max_odometer=Max('odometer'))['max_odometer']
        current_odometer = max_odometer or car.initial_odometer

        return Response({
            'car': car.name,
            'current_odometer': current_odometer,
            'total_spent': total_spent,
            'by_category': by_category,
        })


class RecordListCreateView(generics.ListCreateAPIView):
    serializer_class = RecordSerializer
    pagination_class = StandardResultsSetPagination

    @extend_schema(parameters=[
        OpenApiParameter('car', int),
        OpenApiParameter('category', str),
    ])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Record.objects.none()
        queryset = Record.objects.filter(car__owner=self.request.user)

        car = self.request.query_params.get('car')
        category = self.request.query_params.get('category')

        if car and car.isdigit():
            queryset = queryset.filter(car_id=car)
        if category:
            queryset = queryset.filter(category=category)
        return queryset


class RecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RecordSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Record.objects.none()
        return Record.objects.filter(car__owner=self.request.user)