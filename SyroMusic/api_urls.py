"""
API URL configuration for SyroMusic app using Django REST Framework.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    ArtistViewSet, AlbumViewSet, SongViewSet, PlaylistViewSet,
    SpotifyUserViewSet, UserStatsViewSet, ListeningActivityViewSet,
    sync_spotify_stats_api, get_stats_detailed_api, track_lyrics_api
)

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'artists', ArtistViewSet, basename='artist')
router.register(r'albums', AlbumViewSet, basename='album')
router.register(r'songs', SongViewSet, basename='song')
router.register(r'playlists', PlaylistViewSet, basename='playlist')
router.register(r'spotify/user', SpotifyUserViewSet, basename='spotify-user')
router.register(r'activity', ListeningActivityViewSet, basename='listening-activity')
router.register(r'stats', UserStatsViewSet, basename='user-stats')

app_name = 'api'

urlpatterns = [
    # Include all router-based URLs
    path('', include(router.urls)),

    # Additional API endpoints
    path('sync/spotify/', sync_spotify_stats_api, name='sync-spotify-stats'),
    path('stats/detailed/', get_stats_detailed_api, name='stats-detailed'),
    path('lyrics/', track_lyrics_api, name='track-lyrics'),
]
