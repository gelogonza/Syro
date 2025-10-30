"""
Serializers for SyroMusic API endpoints using Django REST Framework.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Artist, Album, Song, Playlist,
    SpotifyUser, UserListeningStats, UserListeningActivity
)


# ============================================================
# User & Authentication Serializers
# ============================================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer for Django User model."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class SpotifyUserSerializer(serializers.ModelSerializer):
    """Serializer for SpotifyUser model."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = SpotifyUser
        fields = [
            'id', 'user', 'spotify_id', 'spotify_username', 'spotify_display_name',
            'spotify_email', 'profile_image_url', 'spotify_profile_url',
            'followers_count', 'is_connected', 'last_synced', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'spotify_id', 'access_token', 'refresh_token',
            'token_expires_at', 'last_synced', 'created_at', 'updated_at'
        ]


# ============================================================
# Music Model Serializers
# ============================================================

class ArtistSerializer(serializers.ModelSerializer):
    """Serializer for Artist model."""

    class Meta:
        model = Artist
        fields = ['id', 'name', 'biography', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AlbumSerializer(serializers.ModelSerializer):
    """Serializer for Album model."""
    artist = ArtistSerializer(read_only=True)
    artist_id = serializers.PrimaryKeyRelatedField(
        queryset=Artist.objects.all(),
        write_only=True,
        source='artist'
    )

    class Meta:
        model = Album
        fields = ['id', 'title', 'artist', 'artist_id', 'release_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SongSerializer(serializers.ModelSerializer):
    """Serializer for Song model."""
    album = AlbumSerializer(read_only=True)
    album_id = serializers.PrimaryKeyRelatedField(
        queryset=Album.objects.all(),
        write_only=True,
        source='album'
    )

    class Meta:
        model = Song
        fields = ['id', 'title', 'album', 'album_id', 'duration', 'track_number', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlaylistSerializer(serializers.ModelSerializer):
    """Serializer for Playlist model."""
    user = UserSerializer(read_only=True)
    songs = SongSerializer(many=True, read_only=True)
    song_ids = serializers.PrimaryKeyRelatedField(
        queryset=Song.objects.all(),
        write_only=True,
        source='songs',
        many=True
    )

    class Meta:
        model = Playlist
        fields = ['id', 'title', 'user', 'songs', 'song_ids', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


# ============================================================
# Listening Statistics Serializers
# ============================================================

class UserListeningActivitySerializer(serializers.ModelSerializer):
    """Serializer for UserListeningActivity model."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserListeningActivity
        fields = [
            'id', 'user', 'spotify_track_id', 'track_name', 'artist_name',
            'album_name', 'played_at', 'duration_ms', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class UserListeningStatsSerializer(serializers.ModelSerializer):
    """Serializer for UserListeningStats model."""
    user = UserSerializer(read_only=True)
    recent_activity = serializers.SerializerMethodField()

    class Meta:
        model = UserListeningStats
        fields = [
            'id', 'user',
            'top_artists_short_term', 'top_artists_medium_term', 'top_artists_long_term',
            'top_tracks_short_term', 'top_tracks_medium_term', 'top_tracks_long_term',
            'total_artists_followed', 'total_playlists', 'total_saved_tracks',
            'favorite_genres', 'last_synced', 'created_at',
            'recent_activity'
        ]
        read_only_fields = [
            'id', 'user', 'top_artists_short_term', 'top_artists_medium_term',
            'top_artists_long_term', 'top_tracks_short_term', 'top_tracks_medium_term',
            'top_tracks_long_term', 'total_artists_followed', 'total_playlists',
            'total_saved_tracks', 'favorite_genres', 'last_synced', 'created_at'
        ]

    def get_recent_activity(self, obj):
        """Get the 10 most recent listening activities."""
        recent = UserListeningActivity.objects.filter(
            user=obj.user
        ).order_by('-played_at')[:10]
        return UserListeningActivitySerializer(recent, many=True).data


class StatsDetailedSerializer(serializers.Serializer):
    """Serializer for detailed stats response with time-range specific data."""
    time_range = serializers.CharField()
    period_label = serializers.CharField()
    top_artists = serializers.ListField()
    top_tracks = serializers.ListField()
    total_plays = serializers.IntegerField()
    total_artists = serializers.SerializerMethodField()
    total_tracks = serializers.SerializerMethodField()

    def get_total_artists(self, obj):
        """Get count of top artists."""
        return len(obj.get('top_artists', []))

    def get_total_tracks(self, obj):
        """Get count of top tracks."""
        return len(obj.get('top_tracks', []))


class SyncStatusSerializer(serializers.Serializer):
    """Serializer for sync status response."""
    status = serializers.CharField()
    message = serializers.CharField()
    last_synced = serializers.DateTimeField(required=False)
    task_id = serializers.CharField(required=False)
