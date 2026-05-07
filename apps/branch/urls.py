from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import BranchViewSet, StaffViewSet, KioskViewSet, CounterViewSet, ScreenViewSet, overview

router = DefaultRouter()
router.register('list', BranchViewSet, basename='branch')
router.register('staff', StaffViewSet, basename='staff')
router.register('kiosks', KioskViewSet, basename='kiosk')
router.register('counters', CounterViewSet, basename='counter')
router.register('screens', ScreenViewSet, basename='screen')

urlpatterns = [
    path('overview/', overview, name='branch-overview'),
    path('', include(router.urls)),
]
