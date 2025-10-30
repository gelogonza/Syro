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

from .models import (
    Artist, Album, Song, Playlist,
    SpotifyUser, UserListeningStats, UserListeningActivity
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
