"""Root views for Syro project."""
from django.shortcuts import render


def home(request):
    """Render the home page."""
    return render(request, 'SyroMusic/home.html')
