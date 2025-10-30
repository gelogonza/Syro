"""Views for Syro application."""
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import timedelta

from .models import (
    Artist, Album, Song, Playlist,
    SpotifyUser, UserListeningStats, UserListeningActivity
)
from .services import SpotifyService, TokenManager


def artist_list(request):
    """Display list of all artists."""
    artists = Artist.objects.all()
    return render(request, 'SyroMusic/artist_list.html', {'artists': artists})


def artist_detail(request, artist_id):
    """Display detailed view of a specific artist."""
    try:
        artist = Artist.objects.get(id=artist_id)
        albums = artist.albums.all()

        context = {
            'artist': artist,
            'albums': albums,
        }
        return render(request, 'SyroMusic/artist_detail.html', context)
    except Artist.DoesNotExist:
        messages.error(request, 'Artist not found.')
        return redirect('music:artist_list')


def album_list(request):
    """Display list of all albums."""
    albums = Album.objects.all()
    return render(request, 'SyroMusic/album_list.html', {'albums': albums})


def album_detail(request, album_id):
    """Display detailed view of a specific album."""
    try:
        album = Album.objects.get(id=album_id)
        songs = album.songs.all().order_by('track_number')

        context = {
            'album': album,
            'songs': songs,
        }
        return render(request, 'SyroMusic/album_detail.html', context)
    except Album.DoesNotExist:
        messages.error(request, 'Album not found.')
        return redirect('music:album_list')


def song_list(request):
    """Display list of all songs."""
    songs = Song.objects.all()
    return render(request, 'SyroMusic/song_list.html', {'songs': songs})


def song_detail(request, song_id):
    """Display detailed view of a specific song."""
    try:
        song = Song.objects.get(id=song_id)

        context = {
            'song': song,
        }
        return render(request, 'SyroMusic/song_detail.html', context)
    except Song.DoesNotExist:
        messages.error(request, 'Song not found.')
        return redirect('music:song_list')


def playlist_list(request):
    """Display list of all playlists or user's playlists if authenticated."""
    if request.user.is_authenticated:
        playlists = Playlist.objects.filter(user=request.user)
    else:
        playlists = Playlist.objects.none()
    return render(request, 'SyroMusic/playlist_list.html', {'playlists': playlists})


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
    """Initiate Spotify OAuth login flow."""
    try:
        if not all([
            hasattr(__import__('django.conf', fromlist=['settings']).settings, 'SPOTIPY_CLIENT_ID'),
            hasattr(__import__('django.conf', fromlist=['settings']).settings, 'SPOTIPY_CLIENT_SECRET'),
        ]):
            messages.error(request, 'Spotify is not configured. Please contact the administrator.')
            return redirect('login')

        auth_url = SpotifyService.get_authorization_url()
        return redirect(auth_url)
    except Exception as e:
        messages.error(request, f'Error initiating Spotify login: {str(e)}')
        return redirect('login')


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
        sp = SpotifyService(access_token=token_info['access_token'])
        spotify_user_info = sp.get_current_user()

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

        if is_new:
            messages.success(request, f'Welcome to Syro! Your Spotify account has been connected.')
        else:
            messages.success(request, 'Successfully signed in with Spotify!')

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
        spotify_user = SpotifyUser.objects.filter(user=request.user).first()
        listening_stats = UserListeningStats.objects.filter(user=request.user).first()

        context = {
            'spotify_user': spotify_user,
            'listening_stats': listening_stats,
        }
        return render(request, 'SyroMusic/dashboard.html', context)
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('home')


@login_required(login_url='login')
def sync_spotify_stats(request):
    """Trigger a manual sync of Spotify statistics."""
    try:
        from .tasks import sync_all_user_data

        # Trigger the background sync task
        sync_all_user_data.delay(request.user.id)

        messages.success(request, 'Syncing your Spotify stats... This may take a minute.')
        return redirect('music:dashboard')
    except Exception as e:
        messages.error(request, f'Error syncing stats: {str(e)}')
        return redirect('music:dashboard')


@login_required(login_url='login')
def stats_dashboard(request):
    """Enhanced stats dashboard with top artists, tracks, and listening history."""
    try:
        spotify_user = SpotifyUser.objects.filter(user=request.user).first()
        listening_stats = UserListeningStats.objects.filter(user=request.user).first()

        if not spotify_user or not listening_stats:
            messages.warning(request, 'Please sync your Spotify data first.')
            return redirect('music:dashboard')

        # Determine time range from query param
        time_range = request.GET.get('range', 'medium_term')

        if time_range == 'short_term':
            top_artists = listening_stats.top_artists_short_term
            top_tracks = listening_stats.top_tracks_short_term
            period_label = 'Last 4 Weeks'
        elif time_range == 'long_term':
            top_artists = listening_stats.top_artists_long_term
            top_tracks = listening_stats.top_tracks_long_term
            period_label = 'All Time'
        else:  # medium_term
            top_artists = listening_stats.top_artists_medium_term
            top_tracks = listening_stats.top_tracks_medium_term
            period_label = 'Last 6 Months'

        # Get recent listening activity
        recent_activity = UserListeningActivity.objects.filter(
            user=request.user
        ).order_by('-played_at')[:50]

        # Calculate some metrics
        total_plays = UserListeningActivity.objects.filter(user=request.user).count()

        context = {
            'spotify_user': spotify_user,
            'listening_stats': listening_stats,
            'top_artists': top_artists,
            'top_tracks': top_tracks,
            'recent_activity': recent_activity,
            'time_range': time_range,
            'period_label': period_label,
            'total_plays': total_plays,
        }

        return render(request, 'SyroMusic/stats_dashboard.html', context)
    except Exception as e:
        messages.error(request, f'Error loading stats: {str(e)}')
        return redirect('music:dashboard')


@login_required(login_url='login')
def wrapped_view(request):
    """Spotify Wrapped-style summary of user's listening habits."""
    try:
        from collections import Counter
        from datetime import datetime
        
        spotify_user = SpotifyUser.objects.filter(user=request.user).first()
        listening_stats = UserListeningStats.objects.filter(user=request.user).first()

        if not spotify_user or not listening_stats:
            messages.warning(request, 'Please sync your Spotify data first.')
            return redirect('music:dashboard')

        # Get all-time top artists and tracks
        top_artists = listening_stats.top_artists_long_term or []
        top_tracks = listening_stats.top_tracks_long_term or []
        
        # Extract genres from top artists
        all_genres = []
        for artist in top_artists:
            if isinstance(artist.get('genres'), list):
                all_genres.extend(artist.get('genres', []))
        
        # Count genre occurrences
        genre_counts = Counter(all_genres)
        top_genres = [
            {'name': genre.title(), 'count': count} 
            for genre, count in genre_counts.most_common(10)
        ]
        
        # Get top genre and artist
        top_genre = top_genres[0] if top_genres else None
        top_artist = top_artists[0] if top_artists else None
        
        # Calculate totals
        total_artists = len(top_artists)
        total_tracks = len(top_tracks)
        
        context = {
            'year': datetime.now().year,
            'next_year': datetime.now().year + 1,
            'total_artists': total_artists,
            'total_tracks': total_tracks,
            'top_genre': top_genre,
            'top_genres': top_genres,
            'top_artist': top_artist,
            'top_artists': top_artists[:10],
        }

        return render(request, 'SyroMusic/wrapped.html', context)
    except Exception as e:
        messages.error(request, f'Error loading wrapped: {str(e)}')
        return redirect('music:dashboard')
