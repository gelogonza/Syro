"""Root views for Syro project."""
from django.http import JsonResponse


def home(request):
    """Return API status."""
    return JsonResponse({
        'status': 'ok',
        'message': 'SyroApp API is running',
        'version': '1.0.0'
    })
