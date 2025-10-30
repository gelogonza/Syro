from django.contrib import admin
from .models import (
    Artist, Album, Song, Playlist, UserProfile,
    SpotifyUser, UserListeningStats, UserListeningActivity
)


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('-updated_at',)


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'release_date', 'created_at')
    search_fields = ('title', 'artist__name')
    list_filter = ('release_date', 'created_at')
    ordering = ('-created_at',)


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'album', 'duration', 'track_number', 'created_at')
    search_fields = ('title', 'album__title')
    list_filter = ('album', 'created_at')
    ordering = ('-created_at',)


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    search_fields = ('title', 'user__username')
    list_filter = ('created_at',)
    ordering = ('-updated_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'favorite_genre', 'created_at')
    search_fields = ('user__username',)


@admin.register(SpotifyUser)
class SpotifyUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'spotify_username', 'is_connected', 'last_synced')
    search_fields = ('user__username', 'spotify_username', 'spotify_email')
    list_filter = ('is_connected', 'created_at')
    readonly_fields = ('spotify_id', 'access_token', 'created_at', 'updated_at', 'last_synced')
    ordering = ('-updated_at',)


@admin.register(UserListeningStats)
class UserListeningStatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_playlists', 'total_saved_tracks', 'last_synced')
    search_fields = ('user__username',)
    readonly_fields = (
        'top_artists_short_term', 'top_artists_medium_term', 'top_artists_long_term',
        'top_tracks_short_term', 'top_tracks_medium_term', 'top_tracks_long_term',
        'recently_played_tracks', 'favorite_genres', 'created_at'
    )


@admin.register(UserListeningActivity)
class UserListeningActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'track_name', 'artist_name', 'played_at')
    search_fields = ('user__username', 'track_name', 'artist_name')
    list_filter = ('played_at', 'user')
    readonly_fields = ('created_at',)
    ordering = ('-played_at',)
