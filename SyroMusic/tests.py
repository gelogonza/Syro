import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import SpotifyUser, PlaybackQueue


def make_spotify_user(user):
    """Helper to create a SpotifyUser for testing."""
    return SpotifyUser.objects.create(
        user=user,
        spotify_id='test_spotify_id',
        spotify_username='testuser',
        access_token='test_access_token',
        refresh_token='test_refresh_token',
        token_expires_at=timezone.now() + timezone.timedelta(hours=1),
        is_connected=True,
    )


# ---------------------------------------------------------------------------
# Search API tests
# ---------------------------------------------------------------------------

class SearchAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.spotify_user = make_spotify_user(self.user)
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('music:search_json')

    def test_search_requires_login(self):
        """Unauthenticated requests should be rejected."""
        anon_client = Client()
        response = anon_client.get(self.url, {'q': 'test'})
        # DRF returns 403 for unauthenticated when using IsAuthenticated
        self.assertIn(response.status_code, [401, 403])

    def test_search_empty_query_returns_empty(self):
        """Empty query returns empty lists."""
        response = self.client.get(self.url, {'q': ''})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['songs'], [])
        self.assertEqual(data['artists'], [])
        self.assertEqual(data['albums'], [])

    @patch('SyroMusic.search_views.SpotifyService')
    @patch('SyroMusic.search_views.TokenManager')
    def test_search_returns_spotify_results(self, mock_token_mgr, mock_spotify_cls):
        """Search with valid query returns Spotify track results."""
        mock_token_mgr.refresh_user_token.return_value = 'fresh_token'
        mock_service = MagicMock()
        mock_service.search.return_value = {
            'tracks': {
                'items': [{
                    'id': 'track1',
                    'name': "Don't Stop Me Now",
                    'uri': 'spotify:track:track1',
                    'artists': [{'name': 'Queen'}],
                    'album': {
                        'name': 'Jazz',
                        'images': [{'url': 'https://example.com/cover.jpg'}],
                    },
                    'duration_ms': 209000,
                }]
            },
            'artists': {'items': []},
            'albums': {'items': []},
        }
        mock_spotify_cls.return_value = mock_service

        response = self.client.get(self.url, {'q': "don't stop"})
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(len(data['songs']), 1)
        song = data['songs'][0]
        self.assertEqual(song['title'], "Don't Stop Me Now")
        self.assertEqual(song['artist'], 'Queen')
        self.assertEqual(song['uri'], 'spotify:track:track1')

    @patch('SyroMusic.search_views.SpotifyService')
    def test_search_handles_spotify_error_gracefully(self, mock_spotify_cls):
        """If Spotify API raises an exception, local results still returned."""
        mock_service = MagicMock()
        mock_service.search.side_effect = Exception('Spotify API down')
        mock_spotify_cls.return_value = mock_service

        response = self.client.get(self.url, {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should still return valid structure
        self.assertIn('songs', data)
        self.assertIn('artists', data)
        self.assertIn('albums', data)

    @patch('SyroMusic.search_views.SpotifyService')
    def test_search_no_spotify_user_returns_local_only(self, mock_spotify_cls):
        """User without SpotifyUser gets local-only results without error."""
        user2 = User.objects.create_user(username='nospot', password='pass')
        self.client.login(username='nospot', password='pass')

        response = self.client.get(self.url, {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('songs', data)
        # SpotifyService should not have been instantiated
        mock_spotify_cls.assert_not_called()


# ---------------------------------------------------------------------------
# Queue: add_to_queue tests
# ---------------------------------------------------------------------------

class AddToQueueTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='queueuser', password='testpass123'
        )
        self.spotify_user = make_spotify_user(self.user)
        self.client.login(username='queueuser', password='testpass123')
        self.url = reverse('music:add_to_queue')

    def test_add_to_queue_requires_login(self):
        anon_client = Client()
        response = anon_client.post(
            self.url,
            data=json.dumps({'track_uri': 'spotify:track:abc'}),
            content_type='application/json',
        )
        self.assertIn(response.status_code, [302, 403])

    def test_add_to_queue_missing_uri_returns_error(self):
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_add_to_queue_success(self, mock_spotify_cls):
        """Adding a valid track URI succeeds and stores in local queue."""
        mock_service = MagicMock()
        mock_service.add_to_queue.return_value = True
        mock_spotify_cls.return_value = mock_service

        payload = {
            'track_uri': 'spotify:track:abc123',
            'track_info': {
                'title': "Don't Stop Me Now",
                'artist': 'Queen',
                'album': 'Jazz',
            },
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn("Don't Stop Me Now", data['message'])

        # Verify the track was stored locally
        queue = PlaybackQueue.objects.get(user=self.user)
        self.assertEqual(len(queue.queue_tracks), 1)
        self.assertEqual(queue.queue_tracks[0]['uri'], 'spotify:track:abc123')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_add_to_queue_spotify_failure_returns_error(self, mock_spotify_cls):
        """When Spotify rejects the queue add, return an error response."""
        mock_service = MagicMock()
        mock_service.add_to_queue.return_value = False
        mock_spotify_cls.return_value = mock_service

        payload = {'track_uri': 'spotify:track:abc123'}
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_add_to_queue_multiple_tracks(self, mock_spotify_cls):
        """Adding multiple tracks accumulates them in the local queue."""
        mock_service = MagicMock()
        mock_service.add_to_queue.return_value = True
        mock_spotify_cls.return_value = mock_service

        for i in range(3):
            self.client.post(
                self.url,
                data=json.dumps({'track_uri': f'spotify:track:track{i}', 'track_info': {'title': f'Song {i}'}}),
                content_type='application/json',
            )

        queue = PlaybackQueue.objects.get(user=self.user)
        self.assertEqual(len(queue.queue_tracks), 3)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_add_to_queue_only_allows_post(self, mock_spotify_cls):
        """GET requests to add_to_queue should be rejected."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


# ---------------------------------------------------------------------------
# Queue: get_queue tests
# ---------------------------------------------------------------------------

class GetQueueTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='getqueueuser', password='testpass123'
        )
        self.spotify_user = make_spotify_user(self.user)
        self.client.login(username='getqueueuser', password='testpass123')
        self.url = reverse('music:get_queue')

    def test_get_queue_requires_login(self):
        anon_client = Client()
        response = anon_client.get(self.url)
        self.assertIn(response.status_code, [302, 403])

    @patch('SyroMusic.playback_views.TokenManager')
    @patch('SyroMusic.playback_views.SpotifyService')
    def test_get_queue_empty(self, mock_spotify_cls, mock_token_mgr):
        """Returns empty queue when no tracks have been added."""
        mock_token_mgr.refresh_user_token.return_value = 'fresh_token'
        mock_service = MagicMock()
        mock_service.get_queue.return_value = {'queue': []}
        mock_spotify_cls.return_value = mock_service

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['queue_length'], 0)

    @patch('SyroMusic.playback_views.TokenManager')
    @patch('SyroMusic.playback_views.SpotifyService')
    def test_get_queue_with_spotify_items(self, mock_spotify_cls, mock_token_mgr):
        """Returns formatted track info from Spotify queue."""
        mock_token_mgr.refresh_user_token.return_value = 'fresh_token'
        mock_service = MagicMock()
        mock_service.get_queue.return_value = {
            'queue': [{
                'id': 'track1',
                'uri': 'spotify:track:track1',
                'name': 'Bohemian Rhapsody',
                'artists': [{'name': 'Queen'}],
                'album': {
                    'name': 'A Night at the Opera',
                    'images': [{'url': 'https://example.com/cover.jpg'}],
                },
                'duration_ms': 354000,
            }]
        }
        mock_spotify_cls.return_value = mock_service

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertGreaterEqual(data['queue_length'], 1)
        track = data['queue'][0]
        self.assertEqual(track['name'], 'Bohemian Rhapsody')
        self.assertEqual(track['artists'], 'Queen')

    @patch('SyroMusic.playback_views.TokenManager')
    @patch('SyroMusic.playback_views.SpotifyService')
    def test_get_queue_expired_token_returns_error(self, mock_spotify_cls, mock_token_mgr):
        """Returns 401 when the token cannot be refreshed."""
        mock_token_mgr.refresh_user_token.return_value = None

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data['status'], 'error')


# ---------------------------------------------------------------------------
# Queue: clear_queue tests
# ---------------------------------------------------------------------------

class ClearQueueTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='clearuser', password='testpass123'
        )
        make_spotify_user(self.user)
        self.client.login(username='clearuser', password='testpass123')
        self.url = reverse('music:clear_queue')

        # Pre-populate a queue
        self.queue = PlaybackQueue.objects.create(
            user=self.user,
            queue_tracks=[
                {'uri': 'spotify:track:a', 'title': 'Song A'},
                {'uri': 'spotify:track:b', 'title': 'Song B'},
            ],
        )

    def test_clear_queue_empties_local_queue(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')

        self.queue.refresh_from_db()
        self.assertEqual(self.queue.queue_tracks, [])

    def test_clear_queue_only_allows_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
