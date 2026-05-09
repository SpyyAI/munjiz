from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/agents/', include('apps.agents.urls')),
    # Marketing landing page
    path('landing/', include('apps.dashboard.urls')),
    # Mortgage demo — primary product (root)
    path('', include(('apps.mortgage.urls', 'mortgage'), namespace='mortgage')),
]

# Serve uploaded demo docs in dev
if settings.DEBUG:
    urlpatterns += static('/media/', document_root=getattr(settings, 'MEDIA_ROOT', 'media'))
