from django.urls import path
from .views import today_kpis, comparison, insights

urlpatterns = [
    path('today/', today_kpis, name='analytics-today'),
    path('comparison/', comparison, name='analytics-comparison'),
    path('insights/', insights, name='analytics-insights'),
]
