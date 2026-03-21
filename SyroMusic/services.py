"""
Spotify API Service - Wrapper for Spotify Web API interactions
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class SpotifyService:
    """Service to handle all Spotify API interactions."""

    def __init__(self, spotify_user):
        """Initialize Spotify service with optional access token."""
        self.spotify_user = spotify_user
        self.sp = self._get_client()

    def _get_client(self):
        # Check if token needs refresh
        if self.spotify_user.is_token_expired():
            self._refresh_token()

        return spotipy.Spotify(auth=self.spotify_user.access_token)

    def _refresh_token(self):
        try:
            sp_oauth = SpotifyOAuth(
                client_id=settings.SPOTIPY_CLIENT_ID,
                client_secret=settings.SPOTIPY_CLIENT_SECRET,
                redirect_uri=settings.SPOTIPY_REDIRECT_URI,
                scope="user-read-private user-read-email user-library-read user-top-read user-read-recently-played playlist-modify-public playlist-modify-private user-read-playback-state user-modify-playback-state streaming"
            )
            token_info = sp_oauth.refresh_access_token(self.spotify_user.refresh_token)

            self.spotify_user.access_token = token_info['access_token']
            if 'refresh_token' in token_info:
                self.spotify_user.refresh_token = token_info['refresh_token']
            self.spotify_user.expires_at = timezone.now() + timezone.timedelta(seconds=token_info['expires_in'])
            self.spotify_user.save()
            logger.info(f"Refreshed token for user {self.spotify_user.user.username}")
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise

    def search(self, query, type='track,artist,album', limit=10):
        """
        Search Spotify for tracks, artists, and albums.
        """
        try:
            return self.sp.search(q=query, type=type, limit=limit)
        except Exception as e:
            logger.error(f"Spotify search error: {str(e)}")
            # Try one retry with token refresh if it was an auth error
            try:
                self._refresh_token()
                self.sp = spotipy.Spotify(auth=self.spotify_user.access_token)
                return self.sp.search(q=query, type=type, limit=limit)
            except Exception as retry_error:
                logger.error(f"Retry failed: {str(retry_error)}")
                return None

    def get_current_track(self):
        try:
            return self.sp.current_user_playing_track()
        except Exception as e:
            logger.error(f"Error getting current track: {str(e)}")
            return None

    def get_recently_played(self, limit=20):
        try:
            return self.sp.current_user_recently_played(limit=limit)
        except Exception as e:
            logger.error(f"Error getting recently played: {str(e)}")
            # Try one retry with token refresh if it was an auth error
            try:
                self._refresh_token()
                self.sp = spotipy.Spotify(auth=self.spotify_user.access_token)
                return self.sp.current_user_recently_played(limit=limit)
            except Exception as retry_error:
                logger.error(f"Retry failed for recently played: {str(retry_error)}")
                return None

    def get_top_artists(self, limit=20, time_range='medium_term'):
        try:
            return self.sp.current_user_top_artists(limit=limit, time_range=time_range)
        except Exception as e:
            logger.error(f"Error getting top artists: {str(e)}")
            # Try one retry with token refresh if it was an auth error
            try:
                self._refresh_token()
                self.sp = spotipy.Spotify(auth=self.spotify_user.access_token)
                return self.sp.current_user_top_artists(limit=limit, time_range=time_range)
            except Exception as retry_error:
                logger.error(f"Retry failed for top artists: {str(retry_error)}")
                return None

    def get_top_tracks(self, limit=20, time_range='medium_term'):
        try:
            return self.sp.current_user_top_tracks(limit=limit, time_range=time_range)
        except Exception as e:
            logger.error(f"Error getting top tracks: {str(e)}")
            # Try one retry with token refresh if it was an auth error
            try:
                self._refresh_token()
                self.sp = spotipy.Spotify(auth=self.spotify_user.access_token)
                return self.sp.current_user_top_tracks(limit=limit, time_range=time_range)
            except Exception as retry_error:
                logger.error(f"Retry failed for top tracks: {str(retry_error)}")
                return None

    def get_queue(self):
        try:
            return self.sp.queue()
        except Exception as e:
            logger.error(f"Error getting queue: {str(e)}")
            return None

    def add_to_queue(self, uri):
        try:
            self.sp.add_to_queue(uri)
            return True
        except Exception as e:
            logger.error(f"Error adding to queue: {str(e)}")
            return False

    def create_playlist(self, name, description="", public=True):
        try:
            user_id = self.sp.current_user()['id']
            return self.sp.user_playlist_create(user_id, name, public, description)
        except Exception as e:
            logger.error(f"Error creating playlist: {str(e)}")
            return None

    def add_tracks_to_playlist(self, playlist_id, track_uris):
        try:
            return self.sp.playlist_add_items(playlist_id, track_uris)
        except Exception as e:
            logger.error(f"Error adding tracks to playlist: {str(e)}")
            return None

    def get_user_playlists(self, limit=50):
        try:
            return self.sp.current_user_playlists(limit=limit)
        except Exception as e:
            logger.error(f"Error getting user playlists: {str(e)}")
            return None

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

    def start_playback(self, device_id=None, context_uri=None, uris=None, offset=None):
        """Start or resume playback."""
        try:
            kwargs = {}
            if device_id:
                kwargs['device_id'] = device_id
            if context_uri:
                kwargs['context_uri'] = context_uri
            if uris:
                kwargs['uris'] = uris
            if offset is not None:
                kwargs['offset'] = offset

            logger.info(f"Starting playback with kwargs: {kwargs}")
            self.sp.start_playback(**kwargs)
            return True
        except Exception as e:
            logger.error(f"Error starting playback: {str(e)}")
            # Try refreshing token and retry
            try:
                self._refresh_token()
                self.sp = spotipy.Spotify(auth=self.spotify_user.access_token)
                self.sp.start_playback(**kwargs)
                return True
            except Exception as retry_error:
                logger.error(f"Retry failed: {str(retry_error)}")
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

    def transfer_playback(self, device_id, force_play=True):
        """Transfer playback to a specific device."""
        try:
            logger.info(f"Transferring playback to device: {device_id}")
            self.sp.transfer_playback(device_id=device_id, force_play=force_play)
            return True
        except Exception as e:
            logger.error(f"Error transferring playback: {str(e)}")
            # Try refreshing token and retry
            try:
                self._refresh_token()
                self.sp = spotipy.Spotify(auth=self.spotify_user.access_token)
                self.sp.transfer_playback(device_id=device_id, force_play=force_play)
                return True
            except Exception as retry_error:
                logger.error(f"Retry failed: {str(retry_error)}")
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

    @staticmethod
    def refresh_access_token(refresh_token):
        """Refresh Spotify access token using refresh token (static method for TokenManager)."""
        try:
            sp_oauth = SpotifyOAuth(
                client_id=settings.SPOTIPY_CLIENT_ID,
                client_secret=settings.SPOTIPY_CLIENT_SECRET,
                redirect_uri=settings.SPOTIPY_REDIRECT_URI,
                scope="user-read-private user-read-email user-library-read user-top-read user-read-recently-played playlist-modify-public playlist-modify-private user-read-playback-state user-modify-playback-state streaming"
            )
            token_info = sp_oauth.refresh_access_token(refresh_token)
            return token_info
        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            return None

    def get_audio_features(self, track_ids):
        """Get audio features for multiple tracks."""
        try:
            if isinstance(track_ids, str):
                track_ids = [track_ids]
            return self.sp.audio_features(track_ids)
        except Exception as e:
            logger.error(f"Error getting audio features: {str(e)}")
            try:
                self._refresh_token()
                self.sp = spotipy.Spotify(auth=self.spotify_user.access_token)
                return self.sp.audio_features(track_ids)
            except Exception as retry_error:
                logger.error(f"Retry failed for audio features: {str(retry_error)}")
                return None

    def get_available_genres(self):
        """Get list of available genre seeds."""
        try:
            result = self.sp.recommendation_genre_seeds()
            return result.get('genres', []) if isinstance(result, dict) else result
        except Exception as e:
            logger.error(f"Error getting available genres: {str(e)}")
            try:
                self._refresh_token()
                self.sp = spotipy.Spotify(auth=self.spotify_user.access_token)
                result = self.sp.recommendation_genre_seeds()
                return result.get('genres', []) if isinstance(result, dict) else result
            except Exception as retry_error:
                logger.error(f"Retry failed for available genres: {str(retry_error)}")
                return None

    def get_recommendations(self, seed_genres=None, seed_artists=None, seed_tracks=None, **kwargs):
        """Get recommendations based on seeds."""
        try:
            return self.sp.recommendations(
                seed_genres=seed_genres,
                seed_artists=seed_artists,
                seed_tracks=seed_tracks,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            try:
                self._refresh_token()
                self.sp = spotipy.Spotify(auth=self.spotify_user.access_token)
                return self.sp.recommendations(
                    seed_genres=seed_genres,
                    seed_artists=seed_artists,
                    seed_tracks=seed_tracks,
                    **kwargs
                )
            except Exception as retry_error:
                logger.error(f"Retry failed for recommendations: {str(retry_error)}")
                return None

    def get_recommendations_by_genre_and_features(self, genre, energy=None, valence=None, limit=20):
        """Get recommendations by genre and audio features."""
        try:
            kwargs = {
                'seed_genres': [genre] if isinstance(genre, str) else genre,
                'limit': limit
            }
            if energy is not None:
                kwargs['target_energy'] = energy
            if valence is not None:
                kwargs['target_valence'] = valence

            result = self.sp.recommendations(**kwargs)
            return result.get('tracks', []) if isinstance(result, dict) else result
        except Exception as e:
            logger.error(f"Error getting recommendations by genre and features: {str(e)}")
            try:
                self._refresh_token()
                self.sp = spotipy.Spotify(auth=self.spotify_user.access_token)
                result = self.sp.recommendations(**kwargs)
                return result.get('tracks', []) if isinstance(result, dict) else result
            except Exception as retry_error:
                logger.error(f"Retry failed for recommendations: {str(retry_error)}")
                return None

    def get_current_user(self):
        """Get current authenticated user's profile information."""
        try:
            return self.sp.current_user()
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            return None

    def get_saved_albums(self, limit=50, offset=0):
        """Get user's saved albums from Spotify."""
        try:
            return self.sp.current_user_saved_albums(limit=limit, offset=offset)
        except Exception as e:
            logger.error(f"Error getting saved albums: {str(e)}")
            try:
                self._refresh_token()
                self.sp = spotipy.Spotify(auth=self.spotify_user.access_token)
                return self.sp.current_user_saved_albums(limit=limit, offset=offset)
            except Exception as retry_error:
                logger.error(f"Retry failed for saved albums: {str(retry_error)}")
                return None

    def get_user_playlists(self, limit=50, offset=0):
        """Get user's playlists from Spotify."""
        try:
            return self.sp.current_user_playlists(limit=limit, offset=offset)
        except Exception as e:
            logger.error(f"Error getting user playlists: {str(e)}")
            try:
                self._refresh_token()
                self.sp = spotipy.Spotify(auth=self.spotify_user.access_token)
                return self.sp.current_user_playlists(limit=limit, offset=offset)
            except Exception as retry_error:
                logger.error(f"Retry failed for user playlists: {str(retry_error)}")
                return None

    def get_playlist_tracks(self, playlist_id, limit=100, offset=0):
        """Get tracks from a specific playlist."""
        try:
            return self.sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
        except Exception as e:
            logger.error(f"Error getting playlist tracks: {str(e)}")
            try:
                self._refresh_token()
                self.sp = spotipy.Spotify(auth=self.spotify_user.access_token)
                return self.sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
            except Exception as retry_error:
                logger.error(f"Retry failed for playlist tracks: {str(retry_error)}")
                return None

    def get_album_tracks(self, album_id, limit=50, offset=0):
        """Get tracks from a specific album."""
        try:
            return self.sp.album_tracks(album_id, limit=limit, offset=offset)
        except Exception as e:
            logger.error(f"Error getting album tracks: {str(e)}")
            try:
                self._refresh_token()
                self.sp = spotipy.Spotify(auth=self.spotify_user.access_token)
                return self.sp.album_tracks(album_id, limit=limit, offset=offset)
            except Exception as retry_error:
                logger.error(f"Retry failed for album tracks: {str(retry_error)}")
                return None

    @staticmethod
    def get_access_token(code):
        """Exchange authorization code for access token (static method for OAuth callback)."""
        try:
            sp_oauth = SpotifyOAuth(
                client_id=settings.SPOTIPY_CLIENT_ID,
                client_secret=settings.SPOTIPY_CLIENT_SECRET,
                redirect_uri=settings.SPOTIPY_REDIRECT_URI,
                scope="user-read-private user-read-email user-library-read user-top-read user-read-recently-played playlist-modify-public playlist-modify-private user-read-playback-state user-modify-playback-state streaming"
            )
            token_info = sp_oauth.get_access_token(code)
            return token_info
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None

    @staticmethod
    def get_user_profile_from_token(access_token):
        """Get user profile from access token (static method for OAuth callback)."""
        try:
            sp = spotipy.Spotify(auth=access_token)
            return sp.current_user()
        except Exception as e:
            logger.error(f"Error getting user profile from token: {str(e)}")
            return None


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


class LyricsService:
    """Service to fetch lyrics from various sources."""
    
    @staticmethod
    def fetch_lyrics(track_name, artist_name):
        """Fetch lyrics from Genius API.

        Tries multiple search strategies:
        1. Full song + artist search
        2. Just song title search
        3. Song with primary artist only (for featured tracks)
        """
        try:
            import lyricsgenius
            from django.conf import settings

            # Get Genius API token from settings
            genius_token = getattr(settings, 'GENIUS_API_TOKEN', None)

            if not genius_token:
                logger.warning("GENIUS_API_TOKEN not configured in settings. Set GENIUS_API_TOKEN environment variable.")
                return None

            # Initialize Genius API with timeout
            genius = lyricsgenius.Genius(
                genius_token,
                verbose=False,
                remove_section_headers=True,
                skip_non_songs=True,
                excluded_terms=["(Remix)", "(Live)"],
                timeout=15
            )

            # Search strategy 1: Full search with track name and artist
            logger.debug(f"Searching Genius for: {track_name} by {artist_name}")
            song = genius.search_song(track_name, artist_name)

            if song and song.lyrics:
                logger.debug(f"Found lyrics for {track_name} by {artist_name}")
                return {
                    'lyrics': song.lyrics,
                    'source': 'genius',
                    'is_explicit': False
                }

            # Search strategy 2: Try with just the track name
            logger.debug(f"Retrying with just track name: {track_name}")
            song = genius.search_song(track_name, artist=None)

            if song and song.lyrics:
                logger.debug(f"Found lyrics (track-only search) for {track_name}")
                return {
                    'lyrics': song.lyrics,
                    'source': 'genius',
                    'is_explicit': False
                }

            # Search strategy 3: Try with primary artist only (for featured tracks)
            # Extract first artist from comma-separated list
            if ',' in artist_name:
                primary_artist = artist_name.split(',')[0].strip()
                logger.debug(f"Retrying with primary artist only: {track_name} by {primary_artist}")
                song = genius.search_song(track_name, primary_artist)

                if song and song.lyrics:
                    logger.debug(f"Found lyrics (primary artist) for {track_name} by {primary_artist}")
                    return {
                        'lyrics': song.lyrics,
                        'source': 'genius',
                        'is_explicit': False
                    }

            logger.warning(f"No lyrics found for {track_name} by {artist_name} after all search attempts")
            return None

        except ImportError as ie:
            logger.error("lyricsgenius library not installed. Install with: pip install lyricsgenius")
            return None
        except Exception as e:
            logger.error(f"Error fetching lyrics from Genius for '{track_name}' by '{artist_name}': {str(e)}", exc_info=True)
            return None
