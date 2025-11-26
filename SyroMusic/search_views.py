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
def search_json_api(request):
    """
    JSON API endpoint for smart search.
    Used by AJAX for real-time search in player and playlists.
    Returns songs, artists, and albums in JSON format with full metadata.
    Requires authentication for security.
    """
    import logging
    logger = logging.getLogger(__name__)

    query = request.GET.get('q', '').strip()

    if not query or len(query) < 2:
        return JsonResponse({
            'status': 'success',
            'songs': [],
            'artists': [],
            'albums': [],
            'message': 'Query must be at least 2 characters'
        })

    try:
        results = {
            'songs': [],
            'artists': [],
            'albums': [],
        }

        # Search local database for songs
        local_songs = Song.objects.filter(
            Q(title__icontains=query) | Q(album__artist__name__icontains=query)
        ).select_related('album', 'album__artist')[:10]

        for song in local_songs:
            # Add validation for required fields
            if song.album and song.album.artist:
                results['songs'].append({
                    'type': 'song',
                    'id': song.id,
                    'title': song.title,
                    'spotify_id': song.spotify_id or '',
                    'uri': f'spotify:track:{song.spotify_id}' if song.spotify_id else None,
                    'album': {
                        'id': song.album.id,
                        'title': song.album.title or 'Unknown Album',
                        'artist': {
                            'id': song.album.artist.id,
                            'name': song.album.artist.name or 'Unknown Artist',
                        },
                        'cover_url': song.album.cover_url or '',
                    },
                })

        # Search local database for artists
        local_artists = Artist.objects.filter(
            Q(name__icontains=query)
        )[:5]

        for artist in local_artists:
            results['artists'].append({
                'type': 'artist',
                'id': artist.id,
                'name': artist.name or 'Unknown',
                'biography': artist.biography or '',
                'image_url': getattr(artist, 'image_url', ''),
            })

        # Search local database for albums
        local_albums = Album.objects.filter(
            Q(title__icontains=query) | Q(artist__name__icontains=query)
        ).select_related('artist')[:5]

        for album in local_albums:
            if album.artist:
                results['albums'].append({
                    'type': 'album',
                    'id': album.id,
                    'title': album.title or 'Unknown Album',
                    'artist': {
                        'id': album.artist.id,
                        'name': album.artist.name or 'Unknown Artist',
                    },
                    'cover_url': album.cover_url or '',
                    'release_date': str(album.release_date) if album.release_date else '',
                })

        # If local results are sparse, search Spotify
        if len(results['songs']) < 8:
            logger.info(f'Local songs < 8, attempting Spotify search for query: {query}')
            try:
                spotify_user = SpotifyUser.objects.filter(user=request.user).first()
                logger.info(f'SpotifyUser found: {spotify_user is not None}')
                if spotify_user:
                    logger.info(f'SpotifyUser connected: {spotify_user.is_connected}')
                    access_token = TokenManager.refresh_user_token(spotify_user)
                    logger.info(f'Access token obtained: {access_token is not None}')
                    if access_token:
                        sp = SpotifyService(access_token=access_token)

                        # Search for tracks on Spotify
                        try:
                            logger.info(f'Calling Spotify search for tracks with query: {query}')
                            spotify_results = sp.search(query, 'track', limit=10)
                            logger.info(f'Spotify results received: {spotify_results is not None}')
                            if spotify_results and 'tracks' in spotify_results:
                                track_count = len(spotify_results['tracks']['items'])
                                logger.info(f'Found {track_count} tracks from Spotify')
                                for track in spotify_results['tracks']['items']:
                                    # Avoid duplicates
                                    spotify_id = track.get('id', '')
                                    if not any(s.get('spotify_id') == spotify_id for s in results['songs']):
                                        if len(results['songs']) < 20:
                                            artist_info = track.get('artists', [{}])[0] if track.get('artists') else {}
                                            album_info = track.get('album', {})

                                            results['songs'].append({
                                                'type': 'track',
                                                'id': spotify_id,
                                                'title': track.get('name', 'Unknown'),
                                                'spotify_id': spotify_id,
                                                'uri': track.get('uri', ''),
                                                'preview_url': track.get('preview_url', ''),
                                                'album': {
                                                    'id': album_info.get('id', ''),
                                                    'title': album_info.get('name', 'Unknown Album'),
                                                    'artist': {
                                                        'id': artist_info.get('id', ''),
                                                        'name': artist_info.get('name', 'Unknown Artist'),
                                                    },
                                                    'cover_url': (album_info.get('images', [{}])[0].get('url', '')
                                                                 if album_info.get('images') else ''),
                                                },
                                            })
                        except Exception as e:
                            logger.warning(f'Spotify track search failed for query "{query}": {str(e)}')

                        # Search for artists on Spotify
                        if len(results['artists']) < 5:
                            try:
                                artist_results = sp.search(query, 'artist', limit=5)
                                if artist_results and 'artists' in artist_results:
                                    for artist in artist_results['artists']['items']:
                                        artist_id = artist.get('id', '')
                                        if not any(a.get('id') == artist_id for a in results['artists']):
                                            results['artists'].append({
                                                'type': 'artist',
                                                'id': artist_id,
                                                'name': artist.get('name', 'Unknown'),
                                                'biography': '',
                                                'image_url': (artist.get('images', [{}])[0].get('url', '')
                                                             if artist.get('images') else ''),
                                            })
                            except Exception as e:
                                logger.warning(f'Spotify artist search failed for query "{query}": {str(e)}')

                        # Search for albums on Spotify
                        if len(results['albums']) < 5:
                            try:
                                album_results = sp.search(query, 'album', limit=5)
                                if album_results and 'albums' in album_results:
                                    for album in album_results['albums']['items']:
                                        album_id = album.get('id', '')
                                        if not any(a.get('id') == album_id for a in results['albums']):
                                            artist_info = album.get('artists', [{}])[0] if album.get('artists') else {}
                                            results['albums'].append({
                                                'type': 'album',
                                                'id': album_id,
                                                'title': album.get('name', 'Unknown'),
                                                'artist': {
                                                    'id': artist_info.get('id', ''),
                                                    'name': artist_info.get('name', 'Unknown'),
                                                },
                                                'cover_url': (album.get('images', [{}])[0].get('url', '')
                                                             if album.get('images') else ''),
                                                'release_date': album.get('release_date', ''),
                                            })
                            except Exception as e:
                                logger.warning(f'Spotify album search failed for query "{query}": {str(e)}')
            except Exception as e:
                logger.error(f'Spotify service error during search for "{query}": {str(e)}')
                # Continue with local results if Spotify fails

        return JsonResponse({
            'status': 'success',
            'songs': results['songs'][:20],
            'artists': results['artists'][:10],
            'albums': results['albums'][:10],
        })

    except Exception as e:
        logger.error(f'Search API error: {str(e)}')
        return JsonResponse({
            'status': 'error',
            'message': 'Search failed. Please try again.'
        }, status=500)


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
