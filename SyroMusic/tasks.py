"""
Celery tasks for background jobs like syncing Spotify data
"""

from celery import shared_task
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
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
        top_artists_response = sp.get_top_artists(time_range=time_range, limit=50)
        if top_artists_response:
            # Handle both dict response with 'items' key and direct list
            top_artists = top_artists_response.get('items', []) if isinstance(top_artists_response, dict) else top_artists_response
            artists_data = [
                {
                    'id': artist['id'],
                    'name': artist['name'],
                    'image': artist['images'][0]['url'] if artist.get('images') else None,
                    'url': artist['external_urls'].get('spotify', ''),
                    'popularity': artist.get('popularity', 0),
                    'genres': artist.get('genres', []),
                }
                for artist in top_artists if isinstance(artist, dict)
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
        top_tracks_response = sp.get_top_tracks(time_range=time_range, limit=50)
        if top_tracks_response:
            # Handle both dict response with 'items' key and direct list
            top_tracks = top_tracks_response.get('items', []) if isinstance(top_tracks_response, dict) else top_tracks_response
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
                for track in top_tracks if isinstance(track, dict)
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
        recently_played_response = sp.get_recently_played(limit=50)
        if recently_played_response:
            # Handle both dict response with 'items' key and direct list
            recently_played = recently_played_response.get('items', []) if isinstance(recently_played_response, dict) else recently_played_response
            
            # Create activity records for new plays
            for item in recently_played:
                if not isinstance(item, dict):
                    continue
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
                for item in recently_played if isinstance(item, dict) and isinstance(item.get('track'), dict)
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

        # Try to get saved tracks using spotipy's current_user_saved_tracks method
        try:
            saved_tracks_response = sp.sp.current_user_saved_tracks(limit=1)
            if saved_tracks_response and isinstance(saved_tracks_response, dict):
                total_saved = saved_tracks_response.get('total', 0)
                listening_stats.total_saved_tracks = total_saved
                listening_stats.save()
                logger.info(f"Successfully synced saved tracks count for user {user.username}: {total_saved}")
        except Exception as inner_e:
            logger.warning(f"Could not get saved tracks count: {str(inner_e)}")

        return True

    except Exception as e:
        logger.error(f"Error syncing saved tracks count for user {user_id}: {str(e)}")
        return False


@shared_task
def calculate_listening_analytics(user_id):
    """
    Calculate listening analytics including total minutes, genres extraction, etc.
    Uses intelligent estimation based on Spotify's top tracks and activity data.
    """
    try:
        from .models import PlaybackHistoryAnalytics
        from datetime import datetime
        
        user = User.objects.get(id=user_id)
        listening_stats = UserListeningStats.objects.get(user=user)
        
        # Get or create analytics record
        analytics, created = PlaybackHistoryAnalytics.objects.get_or_create(user=user)
        
        # Calculate from TRACKED activity (what we have in DB) - this is ACCURATE
        recent_total_ms = UserListeningActivity.objects.filter(user=user).aggregate(
            total=models.Sum('duration_ms')
        )['total'] or 0
        analytics.total_listening_minutes = recent_total_ms // 60000
        
        # Calculate this year's listening minutes - ACCURATE from tracked data
        current_year = datetime.now().year
        year_start = datetime(current_year, 1, 1)
        this_year_ms = UserListeningActivity.objects.filter(
            user=user,
            played_at__gte=year_start
        ).aggregate(total=models.Sum('duration_ms'))['total'] or 0
        
        # Check how much data we've actually tracked
        tracked_count = UserListeningActivity.objects.filter(user=user).count()
        days_tracking = (datetime.now() - analytics.created_at).days if analytics.created_at else 0
        
        # If we have good tracked data (30+ days), use it; otherwise estimate
        if tracked_count < 50 or days_tracking < 30:
            # Not enough tracked data yet - use intelligent estimation
            short_term_tracks = listening_stats.top_tracks_short_term or []
            if short_term_tracks:
                # Estimate based on short-term top tracks (last 4 weeks)
                # Conservative estimate: top track ~30 plays/4 weeks, decreasing by rank
                estimated_4week_ms = 0
                for i, track in enumerate(short_term_tracks[:50]):
                    rank = i + 1
                    estimated_plays = max(3, int(30 * (1 - (rank / 51) ** 0.7)))
                    duration = track.get('duration_ms', 210000)
                    estimated_4week_ms += duration * estimated_plays
                
                # Extrapolate to full year based on weeks elapsed
                weeks_elapsed = max(1, min(52, (datetime.now() - year_start).days // 7))
                estimated_year_ms = int((estimated_4week_ms / 4) * weeks_elapsed)
                
                # Use estimation only if we don't have tracked data
                if this_year_ms == 0:
                    this_year_ms = estimated_year_ms
        
        analytics.total_listening_minutes_this_year = this_year_ms // 60000
        
        # All-time estimation from long-term data (ESTIMATED - not accurate)
        long_term_tracks = listening_stats.top_tracks_long_term or []
        if long_term_tracks and tracked_count < 500:
            # Use conservative estimation based on long-term top tracks
            estimated_alltime_ms = 0
            for i, track in enumerate(long_term_tracks[:50]):
                rank = i + 1
                # Conservative: top track ~200 plays over all time, decreasing by rank
                estimated_plays = max(15, int(200 * (1 - (rank / 51) ** 0.6)))
                duration = track.get('duration_ms', 210000)
                estimated_alltime_ms += duration * estimated_plays
            
            # Add multiplier for songs outside top 50 (conservative 2x)
            estimated_alltime_ms = int(estimated_alltime_ms * 2)
            analytics.estimated_alltime_minutes = estimated_alltime_ms // 60000
        elif tracked_count >= 500:
            # We have enough tracked data! Use actual numbers
            analytics.estimated_alltime_minutes = analytics.total_listening_minutes
        else:
            # Fallback: conservative estimate
            analytics.estimated_alltime_minutes = analytics.total_listening_minutes_this_year * 2
        
        # Count unique artists and tracks
        analytics.unique_artists_heard = UserListeningActivity.objects.filter(
            user=user
        ).values('artist_name').distinct().count()
        
        analytics.unique_tracks_heard = UserListeningActivity.objects.filter(
            user=user
        ).values('spotify_track_id').distinct().count()
        
        # Extract genres from top artists and store in listening stats
        all_genres = set()
        for term in ['short_term', 'medium_term', 'long_term']:
            artists = getattr(listening_stats, f'top_artists_{term}', [])
            for artist in artists:
                if isinstance(artist, dict) and 'genres' in artist:
                    all_genres.update(artist['genres'])
        
        # Count genre occurrences and sort by frequency
        genre_counts = {}
        for term in ['short_term', 'medium_term', 'long_term']:
            artists = getattr(listening_stats, f'top_artists_{term}', [])
            for artist in artists:
                if isinstance(artist, dict) and 'genres' in artist:
                    for genre in artist['genres']:
                        genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Sort genres by frequency and store top genres
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        listening_stats.favorite_genres = [genre for genre, count in sorted_genres[:10]]
        listening_stats.save()
        
        analytics.save()
        logger.info(f"Successfully calculated analytics for user {user.username}: {analytics.total_listening_minutes} minutes")
        return True
        
    except Exception as e:
        logger.error(f"Error calculating analytics for user {user_id}: {str(e)}")
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
        calculate_listening_analytics.delay(user_id)

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
