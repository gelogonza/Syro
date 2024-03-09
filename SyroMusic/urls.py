# SyroMusic/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('artists/', views.artist_list, name='artist_list'),
    path('albums/', views.album_list, name='album_list'),
    path('songs/', views.song_list, name='song_list'),
    path('playlists/', views.playlist_list, name='playlist_list'),
    path('callback/', views.spotify_callback, name='spotify_callback')
]
