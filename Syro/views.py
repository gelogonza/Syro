"""Root views for Syro project."""
from django.shortcuts import render


def home(request):
    """Render landing page."""
    return render(request, 'syromusic/home.html')
