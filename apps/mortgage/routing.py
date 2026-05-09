from django.urls import re_path
from .consumers import MortgageReviewConsumer

websocket_urlpatterns = [
    re_path(r'^ws/application/(?P<application_id>[A-Za-z0-9_-]+)/$', MortgageReviewConsumer.as_asgi()),
]
