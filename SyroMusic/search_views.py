"""
Search and discovery views for SyroMusic application.
Handles search, recommendations, and playlist management.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Artist, Album, Song, Playlist,
    SpotifyUser, UserListeningStats
)
from .services import SpotifyService, TokenManager

logger = logging.getLogger(__name__)


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
            ).select_related('artist')[:10]

        if search_type in ['all', 'track']:
            results['songs'] = Song.objects.filter(
                Q(title__icontains=query) | Q(album__artist__name__icontains=query)
            ).select_related('album', 'album__artist')[:10]

        if search_type in ['all', 'playlist']:
            if request.user.is_authenticated:
                results['playlists'] = Playlist.objects.filter(
                    Q(title__icontains=query),
                    user=request.user
                ).prefetch_related('songs', 'songs__album', 'songs__album__artist')[:10]

        # Also search Spotify if user is authenticated
        if request.user.is_authenticated:
            try:
                spotify_user = SpotifyUser.objects.filter(user=request.user).first()
                if spotify_user:
                    access_token = TokenManager.refresh_user_token(spotify_user)
                    if access_token:
                        sp = SpotifyService(spotify_user)

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_json_api(request):
    """
    API endpoint for search that returns JSON data.
    Searches both local database and Spotify.
    """
    query = request.GET.get('q', '')
    if not query:
        return Response({'songs': [], 'artists': [], 'albums': []})

    logger.info(f"API Search request for: '{query}' by user {request.user.username}")

    # 1. Search Local Database
    local_songs = list(Song.objects.filter(
        Q(title__icontains=query) | 
        Q(artist__name__icontains=query) |
        Q(album__title__icontains=query)
    ).select_related('album', 'artist')[:5])
    
    local_artists = list(Artist.objects.filter(name__icontains=query)[:5])
    local_albums = list(Album.objects.filter(title__icontains=query).select_related('artist')[:5])

    # 2. Search Spotify
    spotify_songs = []
    spotify_artists = []
    spotify_albums = []

    try:
        # Check if user has Spotify linked
        spotify_user = SpotifyUser.objects.get(user=request.user)
        logger.info(f"Found SpotifyUser for {request.user.username}, initializing service...")
        
        service = SpotifyService(spotify_user)
        
        # Call Spotify API
        logger.info(f"Calling Spotify API search for '{query}'...")
        search_results = service.search(query, type='track,artist,album', limit=10)
        
        if search_results:
            logger.info("Spotify API returned data")
            
            # Process Tracks
            if 'tracks' in search_results and 'items' in search_results['tracks']:
                items = search_results['tracks']['items']
                for track in items:
                    if not track: continue
                    
                    # Extract image
                    image_url = ''
                    if track.get('album') and track['album'].get('images') and len(track['album']['images']) > 0:
                        image_url = track['album']['images'][0]['url']
                    
                    # Extract artist
                    artist_name = "Unknown Artist"
                    if track.get('artists') and len(track['artists']) > 0:
                        artist_name = track['artists'][0]['name']
                        
                    spotify_songs.append({
                        'id': track.get('id'),
                        'spotify_id': track.get('id'),
                        'title': track.get('name'),
                        'artist': artist_name,
                        'album': track.get('album', {}).get('name', ''),
                        'cover_url': image_url,
                        'uri': track.get('uri'),
                        'duration_ms': track.get('duration_ms', 0),
                        'source': 'spotify'
                    })

            # Process Artists
            if 'artists' in search_results and 'items' in search_results['artists']:
                items = search_results['artists']['items']
                for artist in items:
                    if not artist: continue
                    image_url = ''
                    if artist.get('images') and len(artist['images']) > 0:
                        image_url = artist['images'][0]['url']
                        
                    spotify_artists.append({
                        'id': artist.get('id'),
                        'name': artist.get('name'),
                        'image_url': image_url,
                        'uri': artist.get('uri'),
                        'source': 'spotify'
                    })

            # Process Albums
            if 'albums' in search_results and 'items' in search_results['albums']:
                items = search_results['albums']['items']
                for album in items:
                    if not album: continue
                    image_url = ''
                    if album.get('images') and len(album['images']) > 0:
                        image_url = album['images'][0]['url']
                    
                    artist_name = "Unknown"
                    if album.get('artists') and len(album['artists']) > 0:
                        artist_name = album['artists'][0]['name']

                    spotify_albums.append({
                        'id': album.get('id'),
                        'title': album.get('name'),
                        'artist': artist_name,
                        'cover_url': image_url,
                        'release_date': album.get('release_date', ''),
                        'uri': album.get('uri'),
                        'source': 'spotify'
                    })
        else:
            logger.warning("Spotify API returned None or empty dictionary")

    except SpotifyUser.DoesNotExist:
        logger.warning(f"No SpotifyUser linked for user {request.user.username} - cannot search Spotify")
    except Exception as e:
        logger.error(f"Error searching Spotify: {str(e)}", exc_info=True)

    # Format local results
    formatted_local_songs = [{
        'id': s.id,
        'spotify_id': s.spotify_id,
        'title': s.title,
        'artist': s.artist.name if s.artist else "Unknown",
        'album': s.album.title if s.album else "",
        'cover_url': s.album.cover_image.url if s.album and s.album.cover_image else "",
        'uri': s.uri,
        'duration_ms': s.duration_ms,
        'source': 'local'
    } for s in local_songs]

    formatted_local_artists = [{
        'id': a.id,
        'name': a.name,
        'image_url': a.image.url if a.image else "",
        'uri': a.uri,
        'source': 'local'
    } for a in local_artists]

    formatted_local_albums = [{
        'id': a.id,
        'title': a.title,
        'artist': a.artist.name if a.artist else "Unknown",
        'cover_url': a.cover_image.url if a.cover_image else "",
        'release_date': a.release_date,
        'uri': a.uri,
        'source': 'local'
    } for a in local_albums]

    # Combine results
    final_songs = formatted_local_songs + spotify_songs
    final_artists = formatted_local_artists + spotify_artists
    final_albums = formatted_local_albums + spotify_albums

    logger.info(f"Returning total: {len(final_songs)} songs, {len(final_artists)} artists, {len(final_albums)} albums")

    return Response({
        'songs': final_songs,
        'artists': final_artists,
        'albums': final_albums
    })


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
        sp = SpotifyService(spotify_user)

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
        sp = SpotifyService(spotify_user)

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
