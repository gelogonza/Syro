"""Views for Syro application."""
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from spotipy.oauth2 import SpotifyOAuth
import logging

from .models import (
    SpotifyUser, UserListeningStats, UserListeningActivity
)
from .services import SpotifyService, TokenManager

logger = logging.getLogger(__name__)


def signup(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


def spotify_login(request):
    """Redirect user to Spotify authorization page."""
    # Updated scope to include all necessary permissions for device control
    scope = (
        'user-read-private '
        'user-read-email '
        'user-library-read '
        'user-top-read '
        'user-read-recently-played '
        'playlist-modify-public '
        'playlist-modify-private '
        'user-read-playback-state '
        'user-modify-playback-state '
        'user-read-currently-playing '
        'streaming '
        'app-remote-control'  # Added for device control
    )
    
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope=scope,
        show_dialog=True
    )
    
    auth_url = sp_oauth.get_authorize_url()
    logger.info(f"Redirecting user {request.user.username} to Spotify auth URL")
    return redirect(auth_url)


def spotify_callback(request):
    """Handle Spotify OAuth callback and create/update user."""
    try:
        code = request.GET.get('code')
        error = request.GET.get('error')

        if error:
            messages.error(request, f'Spotify authentication failed: {error}')
            return redirect('login')

        if not code:
            messages.error(request, 'No authorization code received from Spotify.')
            return redirect('login')

        # Exchange code for tokens
        token_info = SpotifyService.get_access_token(code)

        if not token_info:
            messages.error(request, 'Failed to obtain Spotify access token.')
            return redirect('login')

        # Get Spotify user info
        spotify_user_info = SpotifyService.get_user_profile_from_token(token_info['access_token'])

        if not spotify_user_info:
            messages.error(request, 'Failed to fetch user information from Spotify.')
            return redirect('login')

        spotify_id = spotify_user_info['id']

        # Check if this Spotify account is already linked to a user
        try:
            spotify_user = SpotifyUser.objects.get(spotify_id=spotify_id)
            user = spotify_user.user
            is_new = False
        except SpotifyUser.DoesNotExist:
            # Create new user or link to existing
            email = spotify_user_info.get('email', '')
            username = spotify_user_info.get('display_name', spotify_id).replace(' ', '_')[:30]

            # Ensure username is unique
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=spotify_user_info.get('display_name', '').split()[0] if spotify_user_info.get('display_name') else ''
            )
            is_new = True

        # Create or update SpotifyUser
        token_expires_at = timezone.now() + timedelta(seconds=token_info.get('expires_in', 3600))

        spotify_user, created = SpotifyUser.objects.update_or_create(
            user=user,
            defaults={
                'spotify_id': spotify_id,
                'spotify_username': spotify_user_info.get('display_name', ''),
                'spotify_email': spotify_user_info.get('email', ''),
                'spotify_display_name': spotify_user_info.get('display_name', ''),
                'access_token': token_info['access_token'],
                'refresh_token': token_info.get('refresh_token', ''),
                'token_expires_at': token_expires_at,
                'profile_image_url': spotify_user_info.get('images', [{}])[0].get('url', '') if spotify_user_info.get('images') else '',
                'spotify_profile_url': spotify_user_info.get('external_urls', {}).get('spotify', ''),
                'followers_count': spotify_user_info.get('followers', {}).get('total', 0),
                'is_connected': True,
            }
        )

        # Create or update listening stats
        UserListeningStats.objects.get_or_create(user=user)

        # Log the user in
        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Trigger automatic sync of Spotify data synchronously
        try:
            from .tasks import (
                sync_user_profile_data,
                sync_user_spotify_stats,
                sync_user_recently_played,
                sync_user_saved_tracks_count,
                calculate_listening_analytics
            )
            
            logger.info(f"Starting automatic sync for user {user.username}")
            sync_user_profile_data(user.id)
            sync_user_spotify_stats(user.id, 'short_term')
            sync_user_spotify_stats(user.id, 'medium_term')
            sync_user_spotify_stats(user.id, 'long_term')
            sync_user_recently_played(user.id)
            sync_user_saved_tracks_count(user.id)
            calculate_listening_analytics(user.id)
            logger.info(f"Completed automatic sync for user {user.username}")
        except Exception as sync_error:
            logger.warning(f"Could not complete automatic sync: {sync_error}")

        if is_new:
            messages.success(request, f'Welcome to Syro! Your Spotify account has been connected and your music data has been synced.')
        else:
            messages.success(request, 'Successfully signed in with Spotify! Your latest data has been synced.')

        return redirect('music:dashboard')

    except Exception as e:
        messages.error(request, f'An error occurred during Spotify authentication: {str(e)}')
        return redirect('login')


@login_required(login_url='login')
def spotify_disconnect(request):
    """Disconnect Spotify account from user."""
    try:
        if request.method == 'POST':
            spotify_user = SpotifyUser.objects.filter(user=request.user).first()
            if spotify_user:
                spotify_user.is_connected = False
                spotify_user.save()
                messages.success(request, 'Spotify account disconnected successfully.')
            return redirect('music:dashboard')
    except Exception as e:
        messages.error(request, f'Error disconnecting Spotify: {str(e)}')
        return redirect('music:dashboard')


@login_required(login_url='login')
def dashboard(request):
    """User dashboard with Spotify profile and stats."""
    try:
        from .models import PlaybackHistoryAnalytics
        
        spotify_user = SpotifyUser.objects.filter(user=request.user).first()
        listening_stats = UserListeningStats.objects.filter(user=request.user).first()
        analytics = PlaybackHistoryAnalytics.objects.filter(user=request.user).first()
        
        # Get top artist from listening stats
        top_artist = None
        if listening_stats:
            # Try medium term first, then short term, then long term
            for term in ['medium_term', 'short_term', 'long_term']:
                artists = getattr(listening_stats, f'top_artists_{term}', [])
                if artists and len(artists) > 0:
                    top_artist = artists[0].get('name', 'N/A') if isinstance(artists[0], dict) else 'N/A'
                    break
        
        # Get top genre from favorite genres
        top_genre = None
        if listening_stats and listening_stats.favorite_genres:
            top_genre = listening_stats.favorite_genres[0] if isinstance(listening_stats.favorite_genres, list) and len(listening_stats.favorite_genres) > 0 else None

        # Calculate listening minutes with accuracy tracking
        from datetime import datetime
        year_minutes = 0
        alltime_minutes = 0
        is_estimated = True
        tracking_since = None
        
        if analytics:
            year_minutes = analytics.total_listening_minutes_this_year
            alltime_minutes = analytics.estimated_alltime_minutes
            tracking_since = analytics.created_at
            
            # If we've been tracking for a while, use accurate data
            tracked_activities = UserListeningActivity.objects.filter(user=request.user).count()
            if tracked_activities > 100:  # More than 100 plays tracked
                is_estimated = False

        context = {
            'spotify_user': spotify_user,
            'listening_stats': listening_stats,
            'analytics': analytics,
            'top_artist': top_artist,
            'top_genre': top_genre,
            'year_minutes': year_minutes,
            'alltime_minutes': alltime_minutes,
            'is_estimated': is_estimated,
            'tracking_since': tracking_since,
        }
        return render(request, 'syromusic/dashboard.html', context)
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('home')


@login_required(login_url='login')
def sync_spotify_stats(request):
    """Trigger a manual sync of Spotify statistics. Falls back to synchronous execution if Celery unavailable."""
    try:
        from .tasks import (
            sync_user_profile_data,
            sync_user_spotify_stats as sync_stats,
            sync_user_recently_played,
            sync_user_saved_tracks_count,
            calculate_listening_analytics
        )

        # Always run synchronously to avoid Redis/Celery connection issues
        logger.info(f"Starting synchronous sync for user {request.user.id}")
        
        # Execute sync tasks synchronously
        sync_user_profile_data(request.user.id)
        sync_stats(request.user.id, 'short_term')
        sync_stats(request.user.id, 'medium_term')
        sync_stats(request.user.id, 'long_term')
        sync_user_recently_played(request.user.id)
        sync_user_saved_tracks_count(request.user.id)
        calculate_listening_analytics(request.user.id)

        messages.success(request, 'Your Spotify stats have been synced successfully!')
        return redirect('music:dashboard')

    except Exception as e:
        logger.error(f"Error syncing stats for user {request.user.id}: {str(e)}")
        messages.error(request, f'Error syncing stats: {str(e)}')
        return redirect('music:dashboard')
