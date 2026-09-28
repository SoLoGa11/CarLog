from django.urls import path

from .views import (
    CarListCreateView, CarDetailView, CarSetMainView, CarStatsView,
    RecordListCreateView, RecordDetailView,
)

urlpatterns = [
    path('cars/', CarListCreateView.as_view(), name='car-list'),
    path('cars/<int:pk>/', CarDetailView.as_view(), name='car-detail'),
    path('cars/<int:pk>/set-main/', CarSetMainView.as_view(), name='car-set-main'),
    path('cars/<int:pk>/stats/', CarStatsView.as_view(), name='car-stats'),
    path('records/', RecordListCreateView.as_view(), name='record-list'),
    path('records/<int:pk>/', RecordDetailView.as_view(), name='record-detail'),
]