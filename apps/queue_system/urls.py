from django.urls import path
from .views import snapshot, predictions, sla

urlpatterns = [
    path('snapshot/', snapshot, name='queue-snapshot'),
    path('predictions/', predictions, name='queue-predictions'),
    path('sla/', sla, name='queue-sla'),
]
