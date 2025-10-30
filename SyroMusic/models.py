# SyroMusic/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import json
import os
from base64 import b64encode, b64decode
from cryptography.fernet import Fernet

class Artist(models.Model):
    """Model representing a music artist."""
    name = models.CharField(max_length=255, unique=True, db_index=True)
    biography = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Album(models.Model):
    """Model representing a music album."""
    title = models.CharField(max_length=255, db_index=True)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='albums')
    release_date = models.DateField(db_index=True)
    cover_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.title} by {self.artist.name}"

    class Meta:
        ordering = ['-release_date']

class Song(models.Model):
    """Model representing a song."""
    title = models.CharField(max_length=255, db_index=True)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='songs')
    duration = models.DurationField()
    track_number = models.IntegerField(null=True, blank=True)
    spotify_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.title} from {self.album.title}"

    class Meta:
        ordering = ['album', 'track_number', 'title']

class EncryptedField(models.TextField):
    """Custom field to encrypt and decrypt sensitive data."""

    @staticmethod
    def get_cipher():
        """Get or create Fernet cipher for encryption."""
        secret_key = getattr(settings, 'DJANGO_SECRET_KEY', settings.SECRET_KEY)
        # Generate a stable key from the Django SECRET_KEY
        key = b64encode(secret_key.encode()[:32].ljust(32, b'0'))[:44]
        try:
            return Fernet(key)
        except Exception:
            # Fallback for invalid key
            return None

    def get_prep_value(self, value):
        """Encrypt value before saving to database."""
        if value is None:
            return value
        cipher = self.get_cipher()
        if cipher:
            try:
                encrypted = cipher.encrypt(value.encode())
                return encrypted.decode()
            except Exception:
                return value
        return value

    def from_db_value(self, value, expression, connection):
        """Decrypt value retrieved from database."""
        if value is None:
            return value
        cipher = self.get_cipher()
        if cipher:
            try:
                decrypted = cipher.decrypt(value.encode())
                return decrypted.decode()
            except Exception:
                return value
        return value

    def to_python(self, value):
        """Convert database value to Python value."""
        return self.from_db_value(value, None, None)

class Playlist(models.Model):
    """Model representing a user's playlist."""
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    songs = models.ManyToManyField(Song, blank=True, related_name='playlists')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.title} by {self.user.username}"

    class Meta:
        ordering = ['-updated_at']

class UserProfile(models.Model):
    """Extended user profile model for additional user information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    favorite_genre = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    class Meta:
        ordering = ['user']


class SpotifyUser(models.Model):
    """Model to store Spotify user authentication and profile data."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='spotify_user')
    spotify_id = models.CharField(max_length=255, unique=True, db_index=True)
    spotify_username = models.CharField(max_length=255, blank=True)
    spotify_email = models.EmailField(blank=True)
    spotify_display_name = models.CharField(max_length=255, blank=True)

    # Authentication tokens (encrypted)
    access_token = EncryptedField()
    refresh_token = EncryptedField(blank=True, null=True)
    token_expires_at = models.DateTimeField()

    # User profile data from Spotify
    profile_image_url = models.URLField(blank=True, null=True)
    spotify_profile_url = models.URLField(blank=True, null=True)
    followers_count = models.IntegerField(default=0)

    # Connection status
    is_connected = models.BooleanField(default=True)
    last_synced = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Spotify: {self.spotify_username or self.spotify_id}"

    def is_token_expired(self):
        """Check if the access token has expired."""
        return timezone.now() >= self.token_expires_at

    class Meta:
        ordering = ['-updated_at']


class UserListeningStats(models.Model):
    """Model to store user's listening statistics from Spotify."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='listening_stats')

    # Top artists (stored as JSON)
    top_artists_short_term = models.JSONField(default=list, blank=True)  # Last 4 weeks
    top_artists_medium_term = models.JSONField(default=list, blank=True)  # Last 6 months
    top_artists_long_term = models.JSONField(default=list, blank=True)  # All time

    # Top tracks (stored as JSON)
    top_tracks_short_term = models.JSONField(default=list, blank=True)
    top_tracks_medium_term = models.JSONField(default=list, blank=True)
    top_tracks_long_term = models.JSONField(default=list, blank=True)

    # Overall statistics
    total_artists_followed = models.IntegerField(default=0)
    total_playlists = models.IntegerField(default=0)
    total_saved_tracks = models.IntegerField(default=0)

    # Listening patterns
    recently_played_tracks = models.JSONField(default=list, blank=True)  # Last 50 tracks
    favorite_genres = models.JSONField(default=list, blank=True)  # Top genres

    # Sync metadata
    last_synced = models.DateTimeField(auto_now=True)
    synced_short_term = models.DateTimeField(null=True, blank=True)
    synced_medium_term = models.DateTimeField(null=True, blank=True)
    synced_long_term = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Stats for {self.user.username}"

    class Meta:
        ordering = ['-last_synced']


class UserListeningActivity(models.Model):
    """Model to track individual track plays by user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listening_activity')

    # Track information
    spotify_track_id = models.CharField(max_length=255, blank=True)
    track_name = models.CharField(max_length=255)
    artist_name = models.CharField(max_length=255)
    album_name = models.CharField(max_length=255, blank=True)

    # Optional link to local Song model
    song = models.ForeignKey(Song, on_delete=models.SET_NULL, null=True, blank=True)

    # Play information
    played_at = models.DateTimeField()
    duration_ms = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} played {self.track_name}"

    class Meta:
        ordering = ['-played_at']
        indexes = [
            models.Index(fields=['-played_at']),
            models.Index(fields=['user', '-played_at']),
        ]


class SpotifyDevice(models.Model):
    """Model to track user's connected Spotify devices."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='spotify_devices')

    # Device information from Spotify API
    device_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=100)  # Computer, Smartphone, Speaker, etc.

    # Device status
    is_active = models.BooleanField(default=False)
    volume_percent = models.IntegerField(default=100)
    is_private_session = models.BooleanField(default=False)
    supports_volume = models.BooleanField(default=True)

    # Metadata
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s {self.device_name}"

    class Meta:
        ordering = ['-last_seen']
        unique_together = ['user', 'device_id']


class NowPlaying(models.Model):
    """Model to track currently playing track for a user."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='now_playing')

    # Currently playing track info
    spotify_track_id = models.CharField(max_length=255, blank=True)
    track_name = models.CharField(max_length=255, blank=True)
    artist_name = models.CharField(max_length=255, blank=True)
    album_name = models.CharField(max_length=255, blank=True)
    album_image_url = models.URLField(blank=True, null=True)
    spotify_track_url = models.URLField(blank=True, null=True)

    # Playback progress
    duration_ms = models.IntegerField(default=0)
    progress_ms = models.IntegerField(default=0)
    is_playing = models.BooleanField(default=False)
    is_explicit = models.BooleanField(default=False)

    # Device and context
    device = models.ForeignKey(SpotifyDevice, on_delete=models.SET_NULL, null=True, blank=True)
    context_type = models.CharField(max_length=50, blank=True)  # track, playlist, album, artist, etc.
    context_id = models.CharField(max_length=255, blank=True)
    context_name = models.CharField(max_length=255, blank=True)

    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Now playing: {self.track_name or 'Nothing'} for {self.user.username}"

    class Meta:
        ordering = ['-last_updated']


class PlaybackQueue(models.Model):
    """Model to manage user's playback queue."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='playback_queue')

    # Queue information
    queue_tracks = models.JSONField(
        default=list,
        blank=True,
        help_text="List of track objects in queue order"
    )

    # Queue state
    current_index = models.IntegerField(default=0)
    shuffle_enabled = models.BooleanField(default=False)
    repeat_mode = models.CharField(
        max_length=10,
        choices=[
            ('off', 'No Repeat'),
            ('context', 'Repeat All'),
            ('track', 'Repeat One'),
        ],
        default='off'
    )

    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Queue for {self.user.username} ({len(self.queue_tracks)} tracks)"

    def get_current_track(self):
        """Get the current track from the queue."""
        if 0 <= self.current_index < len(self.queue_tracks):
            return self.queue_tracks[self.current_index]
        return None

    def next_track(self):
        """Move to next track in queue."""
        if self.current_index < len(self.queue_tracks) - 1:
            self.current_index += 1
            self.save()
            return self.get_current_track()
        return None

    def previous_track(self):
        """Move to previous track in queue."""
        if self.current_index > 0:
            self.current_index -= 1
            self.save()
            return self.get_current_track()
        return None

    class Meta:
        ordering = ['-last_updated']
