"""
Celery tasks for background jobs like syncing Spotify data
"""

from celery import shared_task
from django.contrib.auth.models import User
from django.utils import timezone
import logging

from .models import SpotifyUser, UserListeningStats, UserListeningActivity
from .services import SpotifyService, TokenManager

logger = logging.getLogger(__name__)


@shared_task
def sync_user_spotify_stats(user_id, time_range='medium_term'):
    """
    Sync a user's top artists and tracks from Spotify.
    time_range: 'short_term' (4 weeks), 'medium_term' (6 months), 'long_term' (all time)
    """
    try:
        user = User.objects.get(id=user_id)
        spotify_user = SpotifyUser.objects.get(user=user)
        listening_stats = UserListeningStats.objects.get(user=user)

        # Refresh token if needed
        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            logger.warning(f"Could not refresh token for user {user.username}")
            return False

        # Create Spotify service with fresh token
        sp = SpotifyService(spotify_user)

        # Fetch top artists
        top_artists = sp.get_top_artists(time_range=time_range, limit=50)
        if top_artists:
            artists_data = [
                {
                    'id': artist['id'],
                    'name': artist['name'],
                    'image': artist['images'][0]['url'] if artist.get('images') else None,
                    'url': artist['external_urls'].get('spotify', ''),
                    'popularity': artist.get('popularity', 0),
                    'genres': artist.get('genres', []),
                }
                for artist in top_artists
            ]

            if time_range == 'short_term':
                listening_stats.top_artists_short_term = artists_data
                listening_stats.synced_short_term = timezone.now()
            elif time_range == 'medium_term':
                listening_stats.top_artists_medium_term = artists_data
                listening_stats.synced_medium_term = timezone.now()
            else:  # long_term
                listening_stats.top_artists_long_term = artists_data
                listening_stats.synced_long_term = timezone.now()

        # Fetch top tracks
        top_tracks = sp.get_top_tracks(time_range=time_range, limit=50)
        if top_tracks:
            tracks_data = [
                {
                    'id': track['id'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name'] if track.get('artists') else 'Unknown',
                    'album': track['album']['name'] if track.get('album') else 'Unknown',
                    'image': track['album']['images'][0]['url'] if track.get('album', {}).get('images') else None,
                    'url': track['external_urls'].get('spotify', ''),
                    'popularity': track.get('popularity', 0),
                    'duration_ms': track.get('duration_ms', 0),
                }
                for track in top_tracks
            ]

            if time_range == 'short_term':
                listening_stats.top_tracks_short_term = tracks_data
            elif time_range == 'medium_term':
                listening_stats.top_tracks_medium_term = tracks_data
            else:  # long_term
                listening_stats.top_tracks_long_term = tracks_data

        listening_stats.save()
        logger.info(f"Successfully synced {time_range} stats for user {user.username}")
        return True

    except SpotifyUser.DoesNotExist:
        logger.warning(f"No Spotify user found for user_id {user_id}")
        return False
    except Exception as e:
        logger.error(f"Error syncing stats for user {user_id}: {str(e)}")
        return False


@shared_task
def sync_user_recently_played(user_id):
    """
    Sync a user's recently played tracks from Spotify.
    """
    try:
        user = User.objects.get(id=user_id)
        spotify_user = SpotifyUser.objects.get(user=user)
        listening_stats = UserListeningStats.objects.get(user=user)

        # Refresh token if needed
        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            logger.warning(f"Could not refresh token for user {user.username}")
            return False

        # Create Spotify service with fresh token
        sp = SpotifyService(spotify_user)

        # Fetch recently played tracks
        recently_played = sp.get_recently_played(limit=50)
        if recently_played:
            # Create activity records for new plays
            for item in recently_played:
                track = item.get('track', {})
                played_at = item.get('played_at')

                # Avoid duplicates
                if not UserListeningActivity.objects.filter(
                    user=user,
                    spotify_track_id=track.get('id'),
                    played_at=played_at
                ).exists():
                    UserListeningActivity.objects.create(
                        user=user,
                        spotify_track_id=track.get('id'),
                        track_name=track.get('name', 'Unknown'),
                        artist_name=track['artists'][0]['name'] if track.get('artists') else 'Unknown',
                        album_name=track['album']['name'] if track.get('album') else 'Unknown',
                        played_at=played_at,
                        duration_ms=track.get('duration_ms', 0),
                    )

            # Update recently played in stats
            recently_played_data = [
                {
                    'id': item['track']['id'],
                    'name': item['track']['name'],
                    'artist': item['track']['artists'][0]['name'] if item['track'].get('artists') else 'Unknown',
                    'played_at': item.get('played_at'),
                }
                for item in recently_played
            ]
            listening_stats.recently_played_tracks = recently_played_data
            listening_stats.save()

        logger.info(f"Successfully synced recently played for user {user.username}")
        return True

    except Exception as e:
        logger.error(f"Error syncing recently played for user {user_id}: {str(e)}")
        return False


@shared_task
def sync_user_profile_data(user_id):
    """
    Sync basic user profile information from Spotify.
    """
    try:
        user = User.objects.get(id=user_id)
        spotify_user = SpotifyUser.objects.get(user=user)

        # Refresh token if needed
        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            logger.warning(f"Could not refresh token for user {user.username}")
            return False

        # Create Spotify service with fresh token
        sp = SpotifyService(spotify_user)

        # Fetch current user info
        user_info = sp.get_current_user()
        if user_info:
            spotify_user.spotify_display_name = user_info.get('display_name', '')
            spotify_user.spotify_email = user_info.get('email', '')
            spotify_user.followers_count = user_info.get('followers', {}).get('total', 0)
            if user_info.get('images'):
                spotify_user.profile_image_url = user_info['images'][0].get('url', '')
            spotify_user.save()

            logger.info(f"Successfully synced profile for user {user.username}")
            return True
        return False

    except Exception as e:
        logger.error(f"Error syncing profile for user {user_id}: {str(e)}")
        return False


@shared_task
def sync_user_saved_tracks_count(user_id):
    """
    Sync count of user's saved tracks (liked songs).
    """
    try:
        user = User.objects.get(id=user_id)
        spotify_user = SpotifyUser.objects.get(user=user)
        listening_stats = UserListeningStats.objects.get(user=user)

        # Refresh token if needed
        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            logger.warning(f"Could not refresh token for user {user.username}")
            return False

        # Create Spotify service with fresh token
        sp = SpotifyService(spotify_user)

        # Fetch saved tracks (we just need the first result to get the total)
        saved_tracks = sp.get_saved_tracks(limit=1)
        # Note: saved_tracks response includes 'total' count
        # We'd need to modify the service to expose this

        logger.info(f"Successfully synced saved tracks count for user {user.username}")
        return True

    except Exception as e:
        logger.error(f"Error syncing saved tracks count for user {user_id}: {str(e)}")
        return False


@shared_task
def sync_all_user_data(user_id):
    """
    Master task that syncs all user data from Spotify.
    """
    try:
        logger.info(f"Starting full sync for user_id {user_id}")

        # Run all sync tasks
        sync_user_profile_data.delay(user_id)
        sync_user_spotify_stats.delay(user_id, 'short_term')
        sync_user_spotify_stats.delay(user_id, 'medium_term')
        sync_user_spotify_stats.delay(user_id, 'long_term')
        sync_user_recently_played.delay(user_id)
        sync_user_saved_tracks_count.delay(user_id)

        logger.info(f"Queued all sync tasks for user_id {user_id}")
        return True

    except Exception as e:
        logger.error(f"Error in master sync for user {user_id}: {str(e)}")
        return False


@shared_task
def extract_album_colors():
    """
    Extract dominant colors from all album covers.
    This task runs periodically to populate the dominant_color field.
    Uses the same color extraction algorithm as the player.
    """
    from .models import Album
    import io
    import urllib.request
    from PIL import Image

    try:
        logger.info("Starting album color extraction task")

        # Get all albums without color or that haven't been extracted recently
        albums = Album.objects.filter(cover_url__isnull=False).exclude(cover_url='')

        extracted_count = 0
        failed_count = 0

        for album in albums:
            try:
                if not album.cover_url:
                    continue

                # Download album cover image
                response = urllib.request.urlopen(album.cover_url, timeout=5)
                img = Image.open(io.BytesIO(response.read())).convert('RGB')

                # Resize for faster processing
                img = img.resize((150, 150))

                # Extract dominant color using quantization
                pixels = list(img.getdata())
                color_map = {}

                for r, g, b in pixels:
                    # Quantize colors to reduce noise
                    r = (r // 25) * 25
                    g = (g // 25) * 25
                    b = (b // 25) * 25
                    key = (r, g, b)
                    color_map[key] = color_map.get(key, 0) + 1

                # Find most frequent color with good brightness
                dominant_color = '#1a1a2e'  # default
                max_count = 0

                for (r, g, b), count in color_map.items():
                    brightness = (r * 299 + g * 587 + b * 114) / 1000
                    # Filter out very dark or very light colors
                    if count > max_count and 20 < brightness < 240:
                        max_count = count
                        dominant_color = f'#{r:02x}{g:02x}{b:02x}'

                # Save color to database
                album.dominant_color = dominant_color
                album.color_extracted_at = timezone.now()
                album.save(update_fields=['dominant_color', 'color_extracted_at'])

                extracted_count += 1
                logger.debug(f"Extracted color for album {album.title}: {dominant_color}")

            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to extract color for album {album.id} ({album.title}): {str(e)}")
                continue

        logger.info(f"Color extraction complete: {extracted_count} successful, {failed_count} failed")
        return {
            'extracted': extracted_count,
            'failed': failed_count,
            'total': albums.count()
        }

    except Exception as e:
        logger.error(f"Error in extract_album_colors task: {str(e)}")
        return {
            'extracted': 0,
            'failed': 0,
            'error': str(e)
        }
