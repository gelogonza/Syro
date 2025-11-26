"""
Spotify API Service - Wrapper for Spotify Web API interactions
"""

from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class SpotifyService:
    """Service to handle all Spotify API interactions."""

    def __init__(self, access_token=None):
        """Initialize Spotify service with optional access token."""
        self.access_token = access_token
        self.sp = Spotify(auth=access_token) if access_token else None

    @staticmethod
    def get_auth_manager():
        """Get SpotifyOAuth manager for authentication."""
        return SpotifyOAuth(
            client_id=settings.SPOTIPY_CLIENT_ID,
            client_secret=settings.SPOTIPY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIPY_REDIRECT_URI,
            scope=[
                'user-read-private',
                'user-read-email',
                'user-read-playback-state',
                'user-modify-playback-state',
                'user-library-read',
                'user-library-modify',
                'playlist-read-private',
                'playlist-read-collaborative',
                'playlist-modify-public',
                'playlist-modify-private',
                'user-top-read',
                'user-read-recently-played',
                'user-follow-read',
                'user-follow-modify',
                'streaming',
            ]
        )

    @staticmethod
    def get_authorization_url():
        """Get the Spotify authorization URL."""
        auth = SpotifyService.get_auth_manager()
        return auth.get_authorize_url()

    @staticmethod
    def get_access_token(code):
        """Exchange authorization code for access token."""
        try:
            auth = SpotifyService.get_auth_manager()
            token_info = auth.get_access_token(code)
            return token_info
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None

    @staticmethod
    def refresh_access_token(refresh_token):
        """Refresh an expired access token using refresh token."""
        try:
            auth = SpotifyService.get_auth_manager()
            token_info = auth.refresh_access_token(refresh_token)
            return token_info
        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            return None

    def get_current_user(self):
        """Get current user profile information."""
        try:
            if not self.sp:
                return None
            user_info = self.sp.current_user()
            return user_info
        except Exception as e:
            logger.error(f"Error fetching current user: {str(e)}")
            return None

    def get_top_artists(self, time_range='medium_term', limit=50):
        """
        Get user's top artists.
        time_range: 'short_term' (4 weeks), 'medium_term' (6 months), 'long_term' (all time)
        """
        try:
            if not self.sp:
                return []
            artists = self.sp.current_user_top_artists(
                time_range=time_range,
                limit=limit
            )
            return artists.get('items', [])
        except Exception as e:
            logger.error(f"Error fetching top artists: {str(e)}")
            return []

    def get_top_tracks(self, time_range='medium_term', limit=50):
        """
        Get user's top tracks.
        time_range: 'short_term' (4 weeks), 'medium_term' (6 months), 'long_term' (all time)
        """
        try:
            if not self.sp:
                return []
            tracks = self.sp.current_user_top_tracks(
                time_range=time_range,
                limit=limit
            )
            return tracks.get('items', [])
        except Exception as e:
            logger.error(f"Error fetching top tracks: {str(e)}")
            return []

    def get_recently_played(self, limit=50):
        """Get user's recently played tracks."""
        try:
            if not self.sp:
                return []
            recent = self.sp.current_user_recently_played(limit=limit)
            return recent.get('items', [])
        except Exception as e:
            logger.error(f"Error fetching recently played: {str(e)}")
            return []

    def get_saved_tracks(self, limit=50, offset=0):
        """Get user's saved tracks (liked songs)."""
        try:
            if not self.sp:
                return []
            tracks = self.sp.current_user_saved_tracks(limit=limit, offset=offset)
            return tracks.get('items', [])
        except Exception as e:
            logger.error(f"Error fetching saved tracks: {str(e)}")
            return []

    def get_audio_features(self, track_ids):
        """
        Get audio features for one or more tracks.
        Spotify limits to 100 tracks per request, so handle batching.
        """
        try:
            if not self.sp or not track_ids:
                return []

            # Batch requests in groups of 100
            all_features = []
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i+100]
                features = self.sp.audio_features(batch)
                all_features.extend([f for f in features if f])  # Filter out None values

            return all_features
        except Exception as e:
            logger.error(f"Error fetching audio features: {str(e)}")
            return []

    def get_available_genres(self):
        """Get list of all available genres from Spotify."""
        try:
            if not self.sp:
                return []
            genres = self.sp.recommendation_genre_seeds()
            return genres.get('genres', [])
        except Exception as e:
            logger.error(f"Error fetching genres: {str(e)}")
            return []

    def get_recommendations_by_genre_and_features(self, genre, energy=None, valence=None, limit=20):
        """
        Get track recommendations based on genre and optional audio features.

        Args:
            genre: Genre seed string
            energy: Target energy (0-1), or None to skip
            valence: Target valence/mood (0-1), or None to skip
            limit: Number of recommendations (max 100)
        """
        try:
            if not self.sp or not genre:
                return []

            kwargs = {
                'seed_genres': [genre],
                'limit': min(limit, 100)
            }

            # Add audio feature targets if provided
            if energy is not None:
                kwargs['target_energy'] = max(0, min(1, energy))
            if valence is not None:
                kwargs['target_valence'] = max(0, min(1, valence))

            recommendations = self.sp.recommendations(**kwargs)
            return recommendations.get('tracks', [])
        except Exception as e:
            logger.error(f"Error fetching recommendations: {str(e)}")
            return []

    def get_current_playlists(self, limit=50):
        """Get user's playlists."""
        try:
            if not self.sp:
                return []
            playlists = self.sp.current_user_playlists(limit=limit)
            return playlists.get('items', [])
        except Exception as e:
            logger.error(f"Error fetching playlists: {str(e)}")
            return []

    def get_playlist_tracks(self, playlist_id, limit=100):
        """Get tracks from a specific playlist."""
        try:
            if not self.sp:
                return []
            tracks = self.sp.playlist_tracks(playlist_id, limit=limit)
            return tracks.get('items', [])
        except Exception as e:
            logger.error(f"Error fetching playlist tracks: {str(e)}")
            return []

    def search(self, query, search_type='track', limit=20):
        """
        Search for tracks, artists, albums, or playlists.
        search_type can be: 'track', 'artist', 'album', 'playlist'
        """
        try:
            if not self.sp:
                return []
            results = self.sp.search(q=query, type=search_type, limit=limit)
            key = f"{search_type}s"
            return results.get(key, {}).get('items', [])
        except Exception as e:
            logger.error(f"Error searching Spotify: {str(e)}")
            return []

    def get_artist_info(self, artist_id):
        """Get detailed information about an artist."""
        try:
            if not self.sp:
                return None
            artist = self.sp.artist(artist_id)
            return artist
        except Exception as e:
            logger.error(f"Error fetching artist info: {str(e)}")
            return None

    def get_album_info(self, album_id):
        """Get detailed information about an album."""
        try:
            if not self.sp:
                return None
            album = self.sp.album(album_id)
            return album
        except Exception as e:
            logger.error(f"Error fetching album info: {str(e)}")
            return None

    def create_playlist(self, name, description='', public=False):
        """Create a new playlist for the user."""
        try:
            if not self.sp:
                return None
            playlist = self.sp.user_playlist_create(
                user=None,  # Current user
                name=name,
                public=public,
                description=description
            )
            return playlist
        except Exception as e:
            logger.error(f"Error creating playlist: {str(e)}")
            return None

    def add_tracks_to_playlist(self, playlist_id, track_ids):
        """Add tracks to a playlist."""
        try:
            if not self.sp:
                return False
            # Spotify API has a limit of 100 tracks per request
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i + 100]
                self.sp.playlist_add_items(playlist_id, batch)
            return True
        except Exception as e:
            logger.error(f"Error adding tracks to playlist: {str(e)}")
            return False

    def remove_tracks_from_playlist(self, playlist_id, track_ids):
        """Remove tracks from a playlist."""
        try:
            if not self.sp:
                return False
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i + 100]
                self.sp.playlist_remove_all_occurrences_of_items(playlist_id, batch)
            return True
        except Exception as e:
            logger.error(f"Error removing tracks from playlist: {str(e)}")
            return False

    def get_track_info(self, track_id):
        """Get detailed information about a track."""
        try:
            if not self.sp:
                return None
            track = self.sp.track(track_id)
            return track
        except Exception as e:
            logger.error(f"Error fetching track info: {str(e)}")
            return None

    def get_recommendations(self, seed_artists=None, seed_tracks=None, seed_genres=None, limit=20):
        """Get recommendations based on seeds."""
        try:
            if not self.sp:
                return []
            recommendations = self.sp.recommendations(
                seed_artists=seed_artists,
                seed_tracks=seed_tracks,
                seed_genres=seed_genres,
                limit=limit
            )
            return recommendations.get('tracks', [])
        except Exception as e:
            logger.error(f"Error fetching recommendations: {str(e)}")
            return []

    # ============================================================
    # Playback Control Methods
    # ============================================================

    def get_current_playback(self):
        """Get current playback state."""
        try:
            if not self.sp:
                return None
            playback = self.sp.current_playback()
            return playback
        except Exception as e:
            logger.error(f"Error fetching current playback: {str(e)}")
            return None

    def get_available_devices(self):
        """Get list of available devices for playback."""
        try:
            if not self.sp:
                return []
            devices = self.sp.devices()
            return devices.get('devices', [])
        except Exception as e:
            logger.error(f"Error fetching devices: {str(e)}")
            return []

    def start_playback(self, context_uri=None, uris=None, device_id=None, offset=0):
        """
        Start playback of a track/album/playlist.
        Either context_uri or uris should be provided.
        """
        try:
            if not self.sp:
                return False
            self.sp.start_playback(
                context_uri=context_uri,
                uris=uris,
                device_id=device_id,
                offset={'position': offset} if offset else None
            )
            return True
        except Exception as e:
            logger.error(f"Error starting playback: {str(e)}")
            return False

    def pause_playback(self, device_id=None):
        """Pause current playback."""
        try:
            if not self.sp:
                return False
            self.sp.pause_playback(device_id=device_id)
            return True
        except Exception as e:
            logger.error(f"Error pausing playback: {str(e)}")
            return False

    def resume_playback(self, device_id=None):
        """Resume playback."""
        try:
            if not self.sp:
                return False
            self.sp.start_playback(device_id=device_id)
            return True
        except Exception as e:
            logger.error(f"Error resuming playback: {str(e)}")
            return False

    def next_track(self, device_id=None):
        """Skip to next track."""
        try:
            if not self.sp:
                return False
            self.sp.next_track(device_id=device_id)
            return True
        except Exception as e:
            logger.error(f"Error skipping to next track: {str(e)}")
            return False

    def previous_track(self, device_id=None):
        """Go to previous track."""
        try:
            if not self.sp:
                return False
            self.sp.previous_track(device_id=device_id)
            return True
        except Exception as e:
            logger.error(f"Error skipping to previous track: {str(e)}")
            return False

    def seek_to_position(self, position_ms, device_id=None):
        """Seek to a specific position in the current track (in milliseconds)."""
        try:
            if not self.sp:
                return False
            self.sp.seek_track(position_ms, device_id=device_id)
            return True
        except Exception as e:
            logger.error(f"Error seeking to position: {str(e)}")
            return False

    def set_volume(self, volume_percent, device_id=None):
        """Set playback volume (0-100)."""
        try:
            if not self.sp:
                return False
            if not 0 <= volume_percent <= 100:
                logger.warning(f"Invalid volume: {volume_percent}. Must be 0-100")
                return False
            self.sp.volume(volume_percent, device_id=device_id)
            return True
        except Exception as e:
            logger.error(f"Error setting volume: {str(e)}")
            return False

    def transfer_playback(self, device_id, play=True):
        """Transfer playback to another device."""
        try:
            if not self.sp:
                return False
            self.sp.transfer_playback(device_id, play=play)
            return True
        except Exception as e:
            logger.error(f"Error transferring playback: {str(e)}")
            return False

    def add_to_queue(self, uri, device_id=None):
        """Add a track to the current queue."""
        try:
            if not self.sp:
                return False
            self.sp.add_to_queue(uri, device_id=device_id)
            return True
        except Exception as e:
            logger.error(f"Error adding to queue: {str(e)}")
            return False

    def get_queue(self):
        """Get the user's current playback queue."""
        try:
            if not self.sp:
                return None
            return self.sp.queue()
        except Exception as e:
            logger.error(f"Error getting queue: {str(e)}")
            return None

    def set_repeat(self, state, device_id=None):
        """
        Set repeat mode.
        state: 'off', 'context' (repeat all), or 'track' (repeat one)
        """
        try:
            if not self.sp:
                return False
            if state not in ['off', 'context', 'track']:
                logger.warning(f"Invalid repeat state: {state}")
                return False
            self.sp.repeat(state, device_id=device_id)
            return True
        except Exception as e:
            logger.error(f"Error setting repeat: {str(e)}")
            return False

    def set_shuffle(self, state, device_id=None):
        """Enable or disable shuffle mode."""
        try:
            if not self.sp:
                return False
            self.sp.shuffle(state, device_id=device_id)
            return True
        except Exception as e:
            logger.error(f"Error setting shuffle: {str(e)}")
            return False


class TokenManager:
    """Manager for handling token encryption/decryption and refresh logic."""

    @staticmethod
    def should_refresh_token(expires_at):
        """Check if token should be refreshed (if it expires in less than 5 minutes)."""
        return timezone.now() >= (expires_at - timedelta(minutes=5))

    @staticmethod
    def refresh_user_token(spotify_user):
        """Refresh a user's Spotify access token if needed."""
        try:
            if not TokenManager.should_refresh_token(spotify_user.token_expires_at):
                return spotify_user.access_token

            if not spotify_user.refresh_token:
                logger.warning(f"No refresh token for user {spotify_user.user.username}")
                return None

            token_info = SpotifyService.refresh_access_token(spotify_user.refresh_token)
            if token_info:
                spotify_user.access_token = token_info['access_token']
                spotify_user.token_expires_at = timezone.now() + timedelta(
                    seconds=token_info.get('expires_in', 3600)
                )
                if 'refresh_token' in token_info:
                    spotify_user.refresh_token = token_info['refresh_token']
                spotify_user.save()
                return spotify_user.access_token
            return None
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None
