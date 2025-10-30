"""Root URL configuration for Syro project."""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from SyroMusic import views as music_views
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('music/', include('SyroMusic.urls')),
    path('api/v1/', include('SyroMusic.api_urls')),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('signup/', music_views.signup, name='signup'),
]
