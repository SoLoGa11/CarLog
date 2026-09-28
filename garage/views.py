from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Car, Record
from .serializers import CarSerializer, RecordSerializer


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

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Record.objects.none()
        return Record.objects.filter(car__owner=self.request.user).select_related('car')


class RecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RecordSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Record.objects.none()
        return Record.objects.filter(car__owner=self.request.user).select_related('car')