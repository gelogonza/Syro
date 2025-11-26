"""URL configuration for Syro app."""
from django.urls import path
from . import views, playback_views, search_views, api_views

app_name = 'music'

urlpatterns = [
    # Dashboard & Profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('sync/', views.sync_spotify_stats, name='sync_spotify_stats'),

    # Spotify OAuth
    path('spotify/login/', views.spotify_login, name='spotify_login'),
    path('spotify/callback/', views.spotify_callback, name='spotify_callback'),
    path('spotify/disconnect/', views.spotify_disconnect, name='spotify_disconnect'),

    # Music Playback & Player
    path('player/', playback_views.player_page, name='player'),
    path('api/playback/state/', playback_views.get_playback_state, name='playback_state'),
    path('api/playback/devices/', playback_views.get_available_devices, name='get_devices'),
    path('api/playback/play/', playback_views.play_track, name='play_track'),
    path('api/playback/pause/', playback_views.play_pause, name='play_pause'),
    path('api/playback/next/', playback_views.next_track, name='next_track'),
    path('api/playback/previous/', playback_views.previous_track, name='previous_track'),
    path('api/playback/seek/', playback_views.seek, name='seek'),
    path('api/playback/volume/', playback_views.set_volume, name='set_volume'),
    path('api/playback/transfer/', playback_views.transfer_playback, name='transfer_playback'),
    path('api/playback/shuffle/', playback_views.set_shuffle, name='set_shuffle'),
    path('api/playback/repeat/', playback_views.set_repeat, name='set_repeat'),
    path('api/playback/queue/add/', playback_views.add_to_queue, name='add_to_queue'),
    path('api/playback/queue/get/', playback_views.get_queue, name='get_queue'),
    path('api/playback/queue/clear/', playback_views.clear_queue, name='clear_queue'),

    # Search & Discovery
    path('search/', search_views.search, name='search'),
    path('api/search/', search_views.search_json_api, name='search_json'),

    # Spotify Playlist Management
    path('api/playlists/user/', api_views.user_playlists_api, name='user_playlists'),
    path('api/playlists/<str:playlist_id>/tracks/', api_views.playlist_tracks_api, name='playlist_tracks'),
    path('api/playlists/add-track/', api_views.add_track_to_playlist_api, name='add_track_to_playlist'),

    # Artist & Album Discovery (Spotify)
    path('api/artists/<str:artist_id>/tracks/', api_views.artist_tracks_api, name='artist_tracks'),
    path('api/albums/tracks/', api_views.album_tracks_api, name='album_tracks'),
    path('api/spotify/album/<str:album_id>/tracks/', api_views.spotify_album_tracks_api, name='spotify_album_tracks'),
]
