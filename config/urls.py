from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/agents/', include('apps.agents.urls')),
    path('api/branch/', include('apps.branch.urls')),
    path('api/customers/', include('apps.customers.urls')),
    path('api/queue/', include('apps.queue_system.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('', include('apps.dashboard.urls')),
]
