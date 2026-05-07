from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import AgentViewSet, ScenarioViewSet

router = DefaultRouter()
router.register('list', AgentViewSet, basename='agent')
router.register('scenarios', ScenarioViewSet, basename='scenario')

urlpatterns = [
    path('', include(router.urls)),
]
