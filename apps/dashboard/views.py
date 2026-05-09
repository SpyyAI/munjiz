"""Marketing landing page for the Munjiz mortgage credit-risk system."""
from django.shortcuts import render
from django.views.decorators.cache import never_cache


@never_cache
def landing(request):
    return render(request, 'landing.html', {})
