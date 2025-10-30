"""
Search and discovery views for SyroMusic application.
Handles search, recommendations, and playlist management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import (
    Artist, Album, Song, Playlist,
    SpotifyUser, UserListeningStats
)
from .services import SpotifyService, TokenManager


def search(request):
    """Main search page with multi-type search."""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')  # all, artist, album, track, playlist

    results = {
        'artists': [],
        'albums': [],
        'songs': [],
        'playlists': [],
    }

    if query and len(query) >= 2:
        # Search local database
        if search_type in ['all', 'artist']:
            results['artists'] = Artist.objects.filter(
                Q(name__icontains=query)
            )[:10]

        if search_type in ['all', 'album']:
            results['albums'] = Album.objects.filter(
                Q(title__icontains=query) | Q(artist__name__icontains=query)
            )[:10]

        if search_type in ['all', 'track']:
            results['songs'] = Song.objects.filter(
                Q(title__icontains=query) | Q(album__artist__name__icontains=query)
            )[:10]

        if search_type in ['all', 'playlist']:
            if request.user.is_authenticated:
                results['playlists'] = Playlist.objects.filter(
                    Q(title__icontains=query),
                    user=request.user
                )[:10]

        # Also search Spotify if user is authenticated
        if request.user.is_authenticated:
            try:
                spotify_user = SpotifyUser.objects.filter(user=request.user).first()
                if spotify_user:
                    access_token = TokenManager.refresh_user_token(spotify_user)
                    if access_token:
                        sp = SpotifyService(access_token=access_token)

                        if search_type in ['all', 'artist']:
                            spotify_artists = sp.search(query, 'artist', limit=5)
                            results['spotify_artists'] = spotify_artists

                        if search_type in ['all', 'album']:
                            spotify_albums = sp.search(query, 'album', limit=5)
                            results['spotify_albums'] = spotify_albums

                        if search_type in ['all', 'track']:
                            spotify_tracks = sp.search(query, 'track', limit=5)
                            results['spotify_tracks'] = spotify_tracks

                        if search_type in ['all', 'playlist']:
                            spotify_playlists = sp.search(query, 'playlist', limit=5)
                            results['spotify_playlists'] = spotify_playlists
            except Exception as e:
                messages.warning(request, f'Could not search Spotify: {str(e)}')

    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
    }
    return render(request, 'SyroMusic/search.html', context)


@login_required(login_url='login')
def recommendations(request):
    """Personalized recommendations based on user's top tracks/artists."""
    try:
        spotify_user = SpotifyUser.objects.filter(user=request.user).first()
        if not spotify_user or not spotify_user.is_connected:
            messages.warning(request, 'Please connect your Spotify account.')
            return redirect('music:dashboard')

        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            messages.error(request, 'Failed to refresh Spotify token.')
            return redirect('music:dashboard')

        listening_stats = UserListeningStats.objects.filter(user=request.user).first()
        sp = SpotifyService(access_token=access_token)

        # Get seed data for recommendations
        seed_artists = []
        seed_tracks = []
        seed_genres = []

        if listening_stats:
            # Extract IDs from top artists and tracks
            top_artists = listening_stats.top_artists_medium_term[:3]
            top_tracks = listening_stats.top_tracks_medium_term[:2]

            if top_artists:
                seed_artists = [a.get('id') for a in top_artists if a.get('id')]
            if top_tracks:
                seed_tracks = [t.get('id') for t in top_tracks if t.get('id')]

        # Get recommendations
        recommendations_data = sp.get_recommendations(
            seed_artists=seed_artists if seed_artists else None,
            seed_tracks=seed_tracks if seed_tracks else None,
            seed_genres=seed_genres if seed_genres else None,
            limit=20
        )

        context = {
            'recommendations': recommendations_data,
            'spotify_user': spotify_user,
        }
        return render(request, 'SyroMusic/recommendations.html', context)

    except Exception as e:
        messages.error(request, f'Error loading recommendations: {str(e)}')
        return redirect('music:dashboard')


@login_required(login_url='login')
def create_playlist(request):
    """Create a new playlist."""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()

        if not title:
            messages.error(request, 'Playlist name is required.')
            return redirect('music:create_playlist')

        try:
            playlist = Playlist.objects.create(
                title=title,
                description=description,
                user=request.user
            )
            messages.success(request, f'Playlist "{title}" created successfully!')
            return redirect('music:playlist_detail', playlist_id=playlist.id)
        except Exception as e:
            messages.error(request, f'Error creating playlist: {str(e)}')
            return redirect('music:create_playlist')

    return render(request, 'SyroMusic/create_playlist.html')


@login_required(login_url='login')
def playlist_detail(request, playlist_id):
    """View and manage a specific playlist."""
    try:
        playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
        songs = playlist.songs.all()

        context = {
            'playlist': playlist,
            'songs': songs,
        }
        return render(request, 'SyroMusic/playlist_detail.html', context)
    except Exception as e:
        messages.error(request, f'Error loading playlist: {str(e)}')
        return redirect('music:playlist_list')


@login_required(login_url='login')
def update_playlist(request, playlist_id):
    """Update playlist details."""
    try:
        playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)

        if request.method == 'POST':
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()

            if not title:
                messages.error(request, 'Playlist name is required.')
                return redirect('music:playlist_detail', playlist_id=playlist_id)

            playlist.title = title
            playlist.description = description
            playlist.save()

            messages.success(request, 'Playlist updated successfully!')
            return redirect('music:playlist_detail', playlist_id=playlist_id)

        context = {'playlist': playlist}
        return render(request, 'SyroMusic/edit_playlist.html', context)

    except Exception as e:
        messages.error(request, f'Error updating playlist: {str(e)}')
        return redirect('music:playlist_list')


@login_required(login_url='login')
def delete_playlist(request, playlist_id):
    """Delete a playlist."""
    try:
        playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)

        if request.method == 'POST':
            title = playlist.title
            playlist.delete()
            messages.success(request, f'Playlist "{title}" deleted successfully!')
            return redirect('music:playlist_list')

        context = {'playlist': playlist}
        return render(request, 'SyroMusic/delete_playlist.html', context)

    except Exception as e:
        messages.error(request, f'Error deleting playlist: {str(e)}')
        return redirect('music:playlist_list')


@login_required(login_url='login')
@require_http_methods(['POST'])
def add_song_to_playlist(request):
    """Add a song to a playlist via AJAX."""
    try:
        playlist_id = request.POST.get('playlist_id')
        song_id = request.POST.get('song_id')

        playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
        song = get_object_or_404(Song, id=song_id)

        if playlist.songs.filter(id=song_id).exists():
            return JsonResponse({
                'status': 'info',
                'message': 'Song already in playlist'
            })

        playlist.songs.add(song)
        return JsonResponse({
            'status': 'success',
            'message': f'"{song.title}" added to playlist'
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required(login_url='login')
@require_http_methods(['POST'])
def remove_song_from_playlist(request):
    """Remove a song from a playlist via AJAX."""
    try:
        playlist_id = request.POST.get('playlist_id')
        song_id = request.POST.get('song_id')

        playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
        song = get_object_or_404(Song, id=song_id)

        playlist.songs.remove(song)
        return JsonResponse({
            'status': 'success',
            'message': f'"{song.title}" removed from playlist'
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required(login_url='login')
def browse_by_genre(request):
    """Browse music by genre/category."""
    try:
        spotify_user = SpotifyUser.objects.filter(user=request.user).first()
        if not spotify_user or not spotify_user.is_connected:
            messages.warning(request, 'Please connect your Spotify account.')
            return redirect('music:dashboard')

        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            messages.error(request, 'Failed to refresh Spotify token.')
            return redirect('music:dashboard')

        # Popular genres to display
        genres = [
            'pop', 'rock', 'hip-hop', 'r-n-b',
            'electronic', 'indie', 'folk', 'country',
            'jazz', 'classical', 'reggae', 'latin'
        ]

        genre_data = []
        sp = SpotifyService(access_token=access_token)

        for genre in genres:
            try:
                recommendations = sp.get_recommendations(
                    seed_genres=[genre],
                    limit=5
                )
                genre_data.append({
                    'name': genre.title(),
                    'tracks': recommendations
                })
            except Exception:
                pass

        context = {
            'genres': genre_data,
            'spotify_user': spotify_user,
        }
        return render(request, 'SyroMusic/browse_genres.html', context)

    except Exception as e:
        messages.error(request, f'Error browsing genres: {str(e)}')
        return redirect('music:dashboard')


@login_required(login_url='login')
def save_track(request, song_id):
    """Save/like a track."""
    try:
        song = get_object_or_404(Song, id=song_id)

        # Save to user's "Liked Tracks" playlist
        saved_playlist, created = Playlist.objects.get_or_create(
            user=request.user,
            title='Liked Tracks',
            defaults={'description': 'Your saved tracks'}
        )

        if saved_playlist.songs.filter(id=song_id).exists():
            messages.info(request, f'"{song.title}" is already in your liked tracks.')
        else:
            saved_playlist.songs.add(song)
            messages.success(request, f'"{song.title}" added to liked tracks!')

        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('music:song_detail', song_id=song_id)

    except Exception as e:
        messages.error(request, f'Error saving track: {str(e)}')
        return redirect(request.META.get('HTTP_REFERER', 'music:song_list'))


@login_required(login_url='login')
def unsave_track(request, song_id):
    """Remove a track from saved."""
    try:
        song = get_object_or_404(Song, id=song_id)

        saved_playlist = Playlist.objects.filter(
            user=request.user,
            title='Liked Tracks'
        ).first()

        if saved_playlist:
            saved_playlist.songs.remove(song)
            messages.success(request, f'"{song.title}" removed from liked tracks.')
        else:
            messages.info(request, 'No liked tracks playlist found.')

        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('music:song_detail', song_id=song_id)

    except Exception as e:
        messages.error(request, f'Error removing track: {str(e)}')
        return redirect(request.META.get('HTTP_REFERER', 'music:song_list'))
