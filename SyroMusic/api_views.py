"""
API Views for SyroMusic using Django REST Framework.
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count

from .models import (
    Artist, Album, Song, Playlist,
    SpotifyUser, UserListeningStats, UserListeningActivity,
    SearchHistory, UserFollowing, PlaylistCollaborator, PlaylistShare,
    PlaybackHistoryAnalytics, QueueItem, TrackLyrics, UserProfile, PlaybackQueue
)
from .serializers import (
    ArtistSerializer, AlbumSerializer, SongSerializer, PlaylistSerializer,
    SpotifyUserSerializer, UserListeningStatsSerializer,
    UserListeningActivitySerializer, SyncStatusSerializer,
    StatsDetailedSerializer
)


# ============================================================
# Pagination Classes
# ============================================================

class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API responses."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    """Pagination for large result sets."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


# ============================================================
# Music Model ViewSets
# ============================================================

class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing artists.
    Supports: list, retrieve
    """
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]
    filterset_fields = ['name']
    search_fields = ['name', 'biography']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class AlbumViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing albums.
    Supports: list, retrieve
    """
    queryset = Album.objects.select_related('artist').all()
    serializer_class = AlbumSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]
    filterset_fields = ['artist', 'release_date']
    search_fields = ['title', 'artist__name']
    ordering_fields = ['title', 'release_date', 'created_at']
    ordering = ['-release_date']


class SongViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing songs.
    Supports: list, retrieve
    """
    queryset = Song.objects.select_related('album', 'album__artist').all()
    serializer_class = SongSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]
    filterset_fields = ['album', 'album__artist']
    search_fields = ['title', 'album__title', 'album__artist__name']
    ordering_fields = ['title', 'created_at']
    ordering = ['album', 'track_number']


class PlaylistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing playlists.
    Supports: list, create, retrieve, update, partial_update, destroy
    Only authenticated users can access their playlists.
    """
    serializer_class = PlaylistSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only playlists owned by the current user."""
        return Playlist.objects.filter(user=self.request.user).prefetch_related(
            'songs', 'songs__album', 'songs__album__artist'
        )

    def perform_create(self, serializer):
        """Create a new playlist for the current user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_track(self, request, pk=None):
        """Add a track to this playlist (Spotify URI or local Song ID)."""
        playlist = self.get_object()
        track_uri = request.data.get('track_uri')
        track_id = request.data.get('track_id')  # Local song ID
        
        if not track_uri and not track_id:
            return Response(
                {'error': 'Either track_uri or track_id must be provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If local track_id provided, add to local playlist
        if track_id:
            try:
                song = get_object_or_404(Song, id=track_id)
                playlist.songs.add(song)
                playlist.save()
            except Exception as e:
                return Response(
                    {'error': f'Error adding track to local playlist: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # If Spotify URI provided, add to Spotify playlist
        if track_uri and playlist.spotify_id:
            try:
                from .services import SpotifyService
                service = SpotifyService(request.user)
                success = service.add_tracks_to_playlist(playlist.spotify_id, [track_uri])
                if not success:
                    return Response(
                        {'error': 'Failed to add track to Spotify playlist'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            except Exception as e:
                return Response(
                    {'error': f'Error adding track to Spotify: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        serializer = self.get_serializer(playlist)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def create_with_spotify(self, request):
        """Create a playlist both locally and on Spotify."""
        name = request.data.get('name')
        description = request.data.get('description', '')
        public = request.data.get('public', False)
        
        if not name:
            return Response(
                {'error': 'Playlist name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from .services import SpotifyService
            service = SpotifyService(request.user)
            
            # Create Spotify playlist
            spotify_playlist = service.create_playlist(name, description, public)
            if not spotify_playlist:
                return Response(
                    {'error': 'Failed to create Spotify playlist'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Create local playlist
            playlist = Playlist.objects.create(
                user=request.user,
                title=name,
                description=description,
                spotify_id=spotify_playlist['id']
            )
            
            serializer = self.get_serializer(playlist)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Error creating playlist: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================
# Statistics & Listening Activity ViewSets
# ============================================================

class ListeningActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retrieving user's listening activity.
    Supports: list, retrieve
    Only authenticated users can access their activity.
    """
    serializer_class = UserListeningActivitySerializer
    pagination_class = LargeResultsSetPagination
    permission_classes = [IsAuthenticated]
    filterset_fields = ['track_name', 'artist_name']
    search_fields = ['track_name', 'artist_name', 'album_name']
    ordering_fields = ['played_at', 'created_at']
    ordering = ['-played_at']

    def get_queryset(self):
        """Return only listening activity for the current user."""
        return UserListeningActivity.objects.filter(
            user=self.request.user
        ).only(
            'track_name', 'artist_name', 'album_name', 'played_at', 'duration_ms', 'spotify_track_id'
        )

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get the 50 most recent listening activities."""
        queryset = self.get_queryset()[:50]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics about listening activity."""
        queryset = self.get_queryset()
        total_plays = queryset.count()
        total_duration = sum(activity.duration_ms for activity in queryset) // 1000 // 60  # Convert to minutes

        # Get unique artists and tracks
        unique_artists = set(activity.artist_name for activity in queryset)
        unique_tracks = set(activity.track_name for activity in queryset)

        return Response({
            'total_plays': total_plays,
            'total_duration_minutes': total_duration,
            'unique_artists': len(unique_artists),
            'unique_tracks': len(unique_tracks),
        })


class UserStatsViewSet(viewsets.ViewSet):
    """
    Custom ViewSet for user listening statistics.
    Supports:
    - list: Get all user stats
    - retrieve: Get specific user stats
    - top_artists: Get top artists for a time range
    - top_tracks: Get top tracks for a time range
    - sync: Trigger a sync operation
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get stats for the current user."""
        user = request.user
        listening_stats = get_object_or_404(UserListeningStats, user=user)
        serializer = UserListeningStatsSerializer(listening_stats)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Get stats for a specific user (admin only for other users)."""
        if pk == 'me':
            pk = request.user.id
        elif pk != str(request.user.id):
            return Response(
                {'detail': 'You can only access your own stats.'},
                status=status.HTTP_403_FORBIDDEN
            )

        user = get_object_or_404(User, pk=pk)
        listening_stats = get_object_or_404(UserListeningStats, user=user)
        serializer = UserListeningStatsSerializer(listening_stats)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def top_artists(self, request):
        """
        Get top artists for a specific time range.
        Query params:
        - time_range: 'short_term' (4 weeks), 'medium_term' (6 months), 'long_term' (all time)
        """
        time_range = request.query_params.get('time_range', 'medium_term')
        user = request.user

        listening_stats = get_object_or_404(UserListeningStats, user=user)

        if time_range == 'short_term':
            top_artists = listening_stats.top_artists_short_term
            period_label = 'Last 4 Weeks'
        elif time_range == 'long_term':
            top_artists = listening_stats.top_artists_long_term
            period_label = 'All Time'
        else:  # medium_term
            top_artists = listening_stats.top_artists_medium_term
            period_label = 'Last 6 Months'

        return Response({
            'time_range': time_range,
            'period_label': period_label,
            'top_artists': top_artists,
            'count': len(top_artists) if top_artists else 0,
        })

    @action(detail=False, methods=['get'])
    def top_tracks(self, request):
        """
        Get top tracks for a specific time range.
        Query params:
        - time_range: 'short_term' (4 weeks), 'medium_term' (6 months), 'long_term' (all time)
        """
        time_range = request.query_params.get('time_range', 'medium_term')
        user = request.user

        listening_stats = get_object_or_404(UserListeningStats, user=user)

        if time_range == 'short_term':
            top_tracks = listening_stats.top_tracks_short_term
            period_label = 'Last 4 Weeks'
        elif time_range == 'long_term':
            top_tracks = listening_stats.top_tracks_long_term
            period_label = 'All Time'
        else:  # medium_term
            top_tracks = listening_stats.top_tracks_medium_term
            period_label = 'Last 6 Months'

        return Response({
            'time_range': time_range,
            'period_label': period_label,
            'top_tracks': top_tracks,
            'count': len(top_tracks) if top_tracks else 0,
        })


# ============================================================
# Spotify & Sync API Views
# ============================================================

class SpotifyUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Spotify user profile information.
    Only authenticated users can access their Spotify profile.
    """
    serializer_class = SpotifyUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only the current user's Spotify profile."""
        user = self.request.user
        return SpotifyUser.objects.filter(user=user)

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get the current user's Spotify profile."""
        try:
            spotify_user = SpotifyUser.objects.get(user=request.user)
            serializer = self.get_serializer(spotify_user)
            return Response(serializer.data)
        except SpotifyUser.DoesNotExist:
            return Response(
                {'detail': 'Spotify account not connected.'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_spotify_stats_api(request):
    """
    API endpoint to trigger a manual sync of Spotify statistics.
    """
    try:
        from .tasks import sync_all_user_data

        # Trigger the background sync task
        task = sync_all_user_data.delay(request.user.id)

        serializer = SyncStatusSerializer({
            'status': 'syncing',
            'message': 'Your Spotify stats are being synced. This may take a minute.',
            'task_id': task.id,
        })
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        return Response(
            {
                'status': 'error',
                'message': f'Error syncing stats: {str(e)}',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stats_detailed_api(request):
    """
    API endpoint to get detailed statistics for a specific time range.
    Query params:
    - time_range: 'short_term' (4 weeks), 'medium_term' (6 months), 'long_term' (all time)
    """
    try:
        time_range = request.query_params.get('time_range', 'medium_term')
        user = request.user

        listening_stats = get_object_or_404(UserListeningStats, user=user)
        total_plays = UserListeningActivity.objects.filter(user=user).count()

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

        data = {
            'time_range': time_range,
            'period_label': period_label,
            'top_artists': top_artists,
            'top_tracks': top_tracks,
            'total_plays': total_plays,
        }

        serializer = StatsDetailedSerializer(data)
        return Response(serializer.data)

    except Exception as e:
        return Response(
            {
                'status': 'error',
                'message': f'Error retrieving stats: {str(e)}',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def search_history_api(request):
    """Search history endpoints."""
    if request.method == 'GET':
        limit = request.query_params.get('limit', 20)
        history = SearchHistory.objects.filter(user=request.user).values('query', 'search_type', 'created_at').distinct()[:int(limit)]
        return Response({
            'status': 'success',
            'data': list(history)
        })

    elif request.method == 'POST':
        query = request.data.get('query', '').strip()
        search_type = request.data.get('search_type', 'all')

        if not query or len(query) < 2:
            return Response(
                {'status': 'error', 'message': 'Query must be at least 2 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )

        SearchHistory.objects.create(
            user=request.user,
            query=query,
            search_type=search_type
        )

        return Response({'status': 'success', 'message': 'Search saved'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_search_history_api(request):
    """Clear all search history for user."""
    SearchHistory.objects.filter(user=request.user).delete()
    return Response({'status': 'success', 'message': 'Search history cleared'})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_profile_api(request):
    """Get or update user profile."""
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        if request.method == 'GET':
            data = {
                'username': request.user.username,
                'email': request.user.email,
                'bio': profile.bio,
                'profile_image': profile.profile_image,
                'favorite_genre': profile.favorite_genre,
                'is_public': profile.is_public,
                'follower_count': profile.user.followers.count(),
                'following_count': profile.user.following.count(),
            }
            return Response({'status': 'success', 'data': data})

        elif request.method == 'POST':
            profile.bio = request.data.get('bio', profile.bio)
            profile.profile_image = request.data.get('profile_image', profile.profile_image)
            profile.favorite_genre = request.data.get('favorite_genre', profile.favorite_genre)
            profile.is_public = request.data.get('is_public', profile.is_public)
            profile.save()

            return Response({'status': 'success', 'message': 'Profile updated'})

    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user_api(request):
    """Follow another user."""
    try:
        username = request.data.get('username')
        target_user = get_object_or_404(User, username=username)

        if target_user == request.user:
            return Response(
                {'status': 'error', 'message': 'Cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        UserFollowing.objects.get_or_create(
            follower=request.user,
            following=target_user
        )

        return Response({'status': 'success', 'message': f'Following {username}'})

    except User.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unfollow_user_api(request):
    """Unfollow another user."""
    try:
        username = request.data.get('username')
        target_user = get_object_or_404(User, username=username)

        UserFollowing.objects.filter(
            follower=request.user,
            following=target_user
        ).delete()

        return Response({'status': 'success', 'message': f'Unfollowed {username}'})

    except User.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def share_playlist_api(request):
    """Share a playlist with another user."""
    try:
        playlist_id = request.data.get('playlist_id')
        username = request.data.get('username')
        message = request.data.get('message', '')

        playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
        shared_with_user = get_object_or_404(User, username=username)

        if shared_with_user == request.user:
            return Response(
                {'status': 'error', 'message': 'Cannot share with yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        PlaylistShare.objects.get_or_create(
            playlist=playlist,
            shared_by=request.user,
            shared_with=shared_with_user,
            defaults={'message': message}
        )

        return Response({'status': 'success', 'message': 'Playlist shared'})

    except Playlist.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'Playlist not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_playlist_collaborator_api(request):
    """Add collaborator to playlist."""
    try:
        playlist_id = request.data.get('playlist_id')
        username = request.data.get('username')
        permission_level = request.data.get('permission_level', 'view')

        playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
        collaborator = get_object_or_404(User, username=username)

        PlaylistCollaborator.objects.update_or_create(
            playlist=playlist,
            user=collaborator,
            defaults={'permission_level': permission_level}
        )

        return Response({'status': 'success', 'message': f'{username} added as collaborator'})

    except (Playlist.DoesNotExist, User.DoesNotExist):
        return Response(
            {'status': 'error', 'message': 'Playlist or user not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def queue_reorder_api(request):
    """Get queue items for reordering."""
    try:
        queue = get_object_or_404(PlaybackQueue, user=request.user)
        items = QueueItem.objects.filter(queue=queue).order_by('position').values('id', 'track_data', 'position')

        return Response({
            'status': 'success',
            'data': list(items)
        })

    except PlaybackQueue.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'Queue not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def queue_reorder_update_api(request):
    """Update queue item positions for drag-and-drop."""
    try:
        queue = get_object_or_404(PlaybackQueue, user=request.user)
        items = request.data.get('items', [])

        for idx, item_id in enumerate(items):
            QueueItem.objects.filter(id=item_id, queue=queue).update(position=idx)

        return Response({'status': 'success', 'message': 'Queue reordered'})

    except PlaybackQueue.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'Queue not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def playback_analytics_api(request):
    """Get detailed playback analytics."""
    try:
        analytics, created = PlaybackHistoryAnalytics.objects.get_or_create(user=request.user)

        data = {
            'listening_streak': analytics.listening_streak,
            'last_listened_date': analytics.last_listened_date,
            'most_active_hour': analytics.most_active_hour,
            'most_active_day_of_week': analytics.most_active_day_of_week,
            'total_listening_minutes': analytics.total_listening_minutes,
            'unique_artists_heard': analytics.unique_artists_heard,
            'unique_tracks_heard': analytics.unique_tracks_heard,
            'monthly_summary': analytics.monthly_summary,
        }

        return Response({'status': 'success', 'data': data})

    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def track_lyrics_api(request):
    """Get lyrics for a track."""
    try:
        spotify_track_id = request.query_params.get('spotify_track_id')

        if not spotify_track_id:
            return Response(
                {'status': 'error', 'message': 'spotify_track_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        lyrics = TrackLyrics.objects.filter(spotify_track_id=spotify_track_id).first()

        if lyrics:
            return Response({
                'status': 'success',
                'data': {
                    'lyrics': lyrics.lyrics,
                    'source': lyrics.lyrics_source,
                    'is_explicit': lyrics.is_explicit,
                }
            })
        else:
            return Response(
                {'status': 'not_found', 'message': 'Lyrics not available'},
                status=status.HTTP_404_NOT_FOUND
            )

    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def albums_by_color_api(request):
    """
    Filter albums by dominant color.
    Query params:
    - color: hex color code (e.g., #ff0000)
    - tolerance: color range tolerance in hex (default: f - includes +/- 15 in each channel)
    Returns: paginated list of albums with that color
    """
    try:
        from .models import Album

        color = request.query_params.get('color', '').strip()

        if not color or not color.startswith('#') or len(color) != 7:
            return Response(
                {'status': 'error', 'message': 'color parameter required (format: #rrggbb)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Query albums by dominant color
        albums = Album.objects.filter(
            dominant_color__iexact=color
        ).select_related('artist').order_by('-release_date')

        # Paginate results
        paginator = Paginator(albums, 20)
        page_number = request.query_params.get('page', 1)
        page_obj = paginator.get_page(page_number)

        album_data = [
            {
                'id': album.id,
                'title': album.title,
                'artist': album.artist.name,
                'artist_id': album.artist.id,
                'cover_url': album.cover_url,
                'release_date': album.release_date.isoformat(),
                'dominant_color': album.dominant_color,
            }
            for album in page_obj.object_list
        ]

        return Response({
            'status': 'success',
            'data': album_data,
            'pagination': {
                'count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })

    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def color_palette_api(request):
    """
    Get all available colors from albums.
    Returns a list of unique dominant colors with counts.
    """
    try:
        from .models import Album

        # Get all unique colors with counts
        color_stats = Album.objects.values('dominant_color').annotate(
            count=Count('id')
        ).order_by('-count')

        colors = [
            {
                'color': stat['dominant_color'],
                'count': stat['count'],
            }
            for stat in color_stats
        ]

        return Response({
            'status': 'success',
            'data': colors,
            'total_unique_colors': len(colors),
        })

    except Exception as e:
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
