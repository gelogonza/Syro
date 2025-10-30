"""URL configuration for Syro app."""
from django.urls import path
from . import views, playback_views, search_views

app_name = 'music'

urlpatterns = [
    # Dashboard & Profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('stats/', views.stats_dashboard, name='stats_dashboard'),
    path('wrapped/', views.wrapped_view, name='wrapped'),
    path('sync/', views.sync_spotify_stats, name='sync_spotify_stats'),

    # List views
    path('artists/', views.artist_list, name='artist_list'),
    path('artists/<int:artist_id>/', views.artist_detail, name='artist_detail'),
    path('albums/', views.album_list, name='album_list'),
    path('albums/<int:album_id>/', views.album_detail, name='album_detail'),
    path('songs/', views.song_list, name='song_list'),
    path('songs/<int:song_id>/', views.song_detail, name='song_detail'),
    path('playlists/', views.playlist_list, name='playlist_list'),

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

    # Search & Discovery
    path('search/', search_views.search, name='search'),
    path('api/search/', search_views.search_json_api, name='search_json'),
    path('recommendations/', search_views.recommendations, name='recommendations'),
    path('browse/genres/', search_views.browse_by_genre, name='browse_genres'),

    # Playlist Management
    path('playlists/create/', search_views.create_playlist, name='create_playlist'),
    path('playlists/<int:playlist_id>/', search_views.playlist_detail, name='playlist_detail'),
    path('playlists/<int:playlist_id>/edit/', search_views.update_playlist, name='update_playlist'),
    path('playlists/<int:playlist_id>/delete/', search_views.delete_playlist, name='delete_playlist'),
    path('api/playlists/add-song/', search_views.add_song_to_playlist, name='add_song_to_playlist'),
    path('api/playlists/remove-song/', search_views.remove_song_from_playlist, name='remove_song_from_playlist'),

    # Track Management
    path('tracks/<int:song_id>/save/', search_views.save_track, name='save_track'),
    path('tracks/<int:song_id>/unsave/', search_views.unsave_track, name='unsave_track'),
]
