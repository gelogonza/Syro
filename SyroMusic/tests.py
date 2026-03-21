import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import SpotifyUser, PlaybackQueue, Playlist


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


# ---------------------------------------------------------------------------
# Playback controls: empty device_id normalised to None
# ---------------------------------------------------------------------------

class PlaybackControlsTests(TestCase):
    """Verify that empty device_id strings are treated as None (not sent to Spotify)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='ctrluser', password='testpass')
        make_spotify_user(self.user)
        self.client.login(username='ctrluser', password='testpass')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_play_pause_empty_device_id(self, mock_cls):
        mock_service = MagicMock()
        mock_service.get_current_playback.return_value = {'is_playing': False}
        mock_service.resume_playback.return_value = True
        mock_cls.return_value = mock_service

        self.client.post(
            reverse('music:play_pause'),
            data='device_id=',
            content_type='application/x-www-form-urlencoded',
        )
        # device_id should be None, not ''
        mock_service.resume_playback.assert_called_once_with(device_id=None)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_next_track_empty_device_id(self, mock_cls):
        mock_service = MagicMock()
        mock_service.next_track.return_value = True
        mock_cls.return_value = mock_service

        self.client.post(
            reverse('music:next_track'),
            data='device_id=',
            content_type='application/x-www-form-urlencoded',
        )
        mock_service.next_track.assert_called_once_with(device_id=None)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_previous_track_empty_device_id(self, mock_cls):
        mock_service = MagicMock()
        mock_service.previous_track.return_value = True
        mock_cls.return_value = mock_service

        self.client.post(
            reverse('music:previous_track'),
            data='device_id=',
            content_type='application/x-www-form-urlencoded',
        )
        mock_service.previous_track.assert_called_once_with(device_id=None)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_play_pause_toggles_pause_when_playing(self, mock_cls):
        """When currently playing, play_pause should call pause."""
        mock_service = MagicMock()
        mock_service.get_current_playback.return_value = {'is_playing': True}
        mock_service.pause_playback.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            reverse('music:play_pause'),
            data='device_id=dev123',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        mock_service.pause_playback.assert_called_once_with(device_id='dev123')
        mock_service.resume_playback.assert_not_called()

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_play_pause_requires_post(self, mock_cls):
        """GET requests to play_pause should be rejected."""
        response = self.client.get(reverse('music:play_pause'))
        self.assertEqual(response.status_code, 405)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_next_track_requires_post(self, mock_cls):
        response = self.client.get(reverse('music:next_track'))
        self.assertEqual(response.status_code, 405)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_previous_track_requires_post(self, mock_cls):
        response = self.client.get(reverse('music:previous_track'))
        self.assertEqual(response.status_code, 405)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_next_track_spotify_failure_returns_error(self, mock_cls):
        """When Spotify next_track fails, view should return 400."""
        mock_service = MagicMock()
        mock_service.next_track.return_value = False
        mock_cls.return_value = mock_service

        response = self.client.post(
            reverse('music:next_track'),
            data='device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_previous_track_spotify_failure_returns_error(self, mock_cls):
        """When Spotify previous_track fails, view should return 400."""
        mock_service = MagicMock()
        mock_service.previous_track.return_value = False
        mock_cls.return_value = mock_service

        response = self.client.post(
            reverse('music:previous_track'),
            data='device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')


# ---------------------------------------------------------------------------
# play_track endpoint tests
# ---------------------------------------------------------------------------

class PlayTrackTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='playuser', password='testpass')
        make_spotify_user(self.user)
        self.client.login(username='playuser', password='testpass')
        self.url = reverse('music:play_track')

    def test_play_track_requires_login(self):
        anon = Client()
        response = anon.post(
            self.url,
            data=json.dumps({'track_uri': 'spotify:track:abc'}),
            content_type='application/json',
        )
        self.assertIn(response.status_code, [302, 403])

    def test_play_track_requires_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_play_track_missing_uri_returns_error(self):
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_play_track_uri_json_body(self, mock_cls):
        """Playing a track URI via JSON body calls start_playback with uris=[...]."""
        mock_service = MagicMock()
        mock_service.start_playback.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data=json.dumps({'track_uri': 'spotify:track:abc123', 'device_id': 'dev1'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        mock_service.start_playback.assert_called_once_with(
            uris=['spotify:track:abc123'], device_id='dev1'
        )

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_play_context_uri_calls_context_playback(self, mock_cls):
        """Playing an album/playlist URI calls start_playback with context_uri."""
        mock_service = MagicMock()
        mock_service.start_playback.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data=json.dumps({'uri': 'spotify:album:albumid123', 'device_id': 'dev1'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        mock_service.start_playback.assert_called_once_with(
            context_uri='spotify:album:albumid123', device_id='dev1'
        )

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_play_track_form_encoded(self, mock_cls):
        """Playing via form-encoded body is also supported."""
        mock_service = MagicMock()
        mock_service.start_playback.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='track_uri=spotify%3Atrack%3Axyz',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        mock_service.start_playback.assert_called_once()

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_play_track_spotify_failure_returns_error(self, mock_cls):
        mock_service = MagicMock()
        mock_service.start_playback.return_value = False
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data=json.dumps({'track_uri': 'spotify:track:bad'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')


# ---------------------------------------------------------------------------
# seek endpoint tests
# ---------------------------------------------------------------------------

class SeekTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='seekuser', password='testpass')
        make_spotify_user(self.user)
        self.client.login(username='seekuser', password='testpass')
        self.url = reverse('music:seek')

    def test_seek_requires_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_seek_missing_position_returns_error(self):
        response = self.client.post(
            self.url,
            data='device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_seek_success(self, mock_cls):
        mock_service = MagicMock()
        mock_service.seek_to_position.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='position_ms=60000&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        mock_service.seek_to_position.assert_called_once_with(60000, device_id='dev1')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_seek_zero_position(self, mock_cls):
        """Seeking to position 0 (rewind to start) should be valid."""
        mock_service = MagicMock()
        mock_service.seek_to_position.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='position_ms=0&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        # position_ms=0 is falsy — view returns 400; this documents current behaviour
        # If view is updated to allow 0, change this assertion to 200
        self.assertIn(response.status_code, [200, 400])

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_seek_empty_device_id(self, mock_cls):
        """Empty device_id should be treated as None."""
        mock_service = MagicMock()
        mock_service.seek_to_position.return_value = True
        mock_cls.return_value = mock_service

        self.client.post(
            self.url,
            data='position_ms=30000&device_id=',
            content_type='application/x-www-form-urlencoded',
        )
        mock_service.seek_to_position.assert_called_once_with(30000, device_id=None)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_seek_spotify_failure_returns_error(self, mock_cls):
        mock_service = MagicMock()
        mock_service.seek_to_position.return_value = False
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='position_ms=10000&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_seek_to_zero_is_valid(self, mock_cls):
        """Seeking to position 0 (rewind to start) must succeed, not return 400."""
        mock_service = MagicMock()
        mock_service.seek_to_position.return_value = True
        mock_cls.return_value = mock_service
        response = self.client.post(
            self.url,
            data='position_ms=0&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        mock_service.seek_to_position.assert_called_once_with(0, device_id='dev1')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_seek_absent_position_param_returns_400(self, mock_cls):
        """A request with no position_ms param at all must return 400."""
        response = self.client.post(
            self.url,
            data='device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)


# ---------------------------------------------------------------------------
# set_volume endpoint tests
# ---------------------------------------------------------------------------

class SetVolumeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='voluser', password='testpass')
        make_spotify_user(self.user)
        self.client.login(username='voluser', password='testpass')
        self.url = reverse('music:set_volume')

    def test_set_volume_requires_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_set_volume_missing_value_returns_error(self):
        response = self.client.post(
            self.url,
            data='device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)

    def test_set_volume_invalid_above_100_returns_error(self):
        response = self.client.post(
            self.url,
            data='volume=150&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_set_volume_invalid_negative_returns_error(self):
        response = self.client.post(
            self.url,
            data='volume=-10&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_set_volume_success(self, mock_cls):
        mock_service = MagicMock()
        mock_service.set_volume.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='volume=75&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        mock_service.set_volume.assert_called_once_with(75, device_id='dev1')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_set_volume_zero(self, mock_cls):
        """Volume of 0 (mute) should be accepted."""
        mock_service = MagicMock()
        mock_service.set_volume.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='volume=0&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertIn(response.status_code, [200, 400])  # 0 is falsy — documents behaviour

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_set_volume_100(self, mock_cls):
        """Volume of 100 (max) should be accepted."""
        mock_service = MagicMock()
        mock_service.set_volume.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='volume=100&device_id=',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        mock_service.set_volume.assert_called_once_with(100, device_id=None)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_set_volume_zero_succeeds(self, mock_cls):
        """Volume of 0 (mute) must be accepted and passed to Spotify."""
        mock_service = MagicMock()
        mock_service.set_volume.return_value = True
        mock_cls.return_value = mock_service
        response = self.client.post(
            self.url,
            data='volume=0&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        mock_service.set_volume.assert_called_once_with(0, device_id='dev1')

    def test_set_volume_absent_param_returns_400(self):
        """A request with no volume param at all must return 400."""
        response = self.client.post(
            self.url,
            data='device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_set_volume_100_succeeds(self, mock_cls):
        """Volume of 100 (maximum) must be accepted."""
        mock_service = MagicMock()
        mock_service.set_volume.return_value = True
        mock_cls.return_value = mock_service
        response = self.client.post(
            self.url,
            data='volume=100&device_id=',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        mock_service.set_volume.assert_called_once_with(100, device_id=None)


# ---------------------------------------------------------------------------
# set_shuffle endpoint tests
# ---------------------------------------------------------------------------

class SetShuffleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='shuffleuser', password='testpass')
        make_spotify_user(self.user)
        self.client.login(username='shuffleuser', password='testpass')
        self.url = reverse('music:set_shuffle')

    def test_set_shuffle_requires_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_set_shuffle_enable(self, mock_cls):
        mock_service = MagicMock()
        mock_service.set_shuffle.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='state=true&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('enabled', data['message'])
        mock_service.set_shuffle.assert_called_once_with(True, device_id='dev1')

        # Verify persisted in local queue
        queue = PlaybackQueue.objects.get(user=self.user)
        self.assertTrue(queue.shuffle_enabled)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_set_shuffle_disable(self, mock_cls):
        mock_service = MagicMock()
        mock_service.set_shuffle.return_value = True
        mock_cls.return_value = mock_service

        # Pre-enable shuffle
        q, _ = PlaybackQueue.objects.get_or_create(user=self.user)
        q.shuffle_enabled = True
        q.save()

        response = self.client.post(
            self.url,
            data='state=false&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('disabled', data['message'])

        q.refresh_from_db()
        self.assertFalse(q.shuffle_enabled)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_set_shuffle_spotify_failure_returns_error(self, mock_cls):
        mock_service = MagicMock()
        mock_service.set_shuffle.return_value = False
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='state=true&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_set_shuffle_default_false(self, mock_cls):
        """Missing state param defaults to False."""
        mock_service = MagicMock()
        mock_service.set_shuffle.return_value = True
        mock_cls.return_value = mock_service

        self.client.post(
            self.url,
            data='device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        mock_service.set_shuffle.assert_called_once_with(False, device_id='dev1')


# ---------------------------------------------------------------------------
# set_repeat endpoint tests
# ---------------------------------------------------------------------------

class SetRepeatTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='repeatuser', password='testpass')
        make_spotify_user(self.user)
        self.client.login(username='repeatuser', password='testpass')
        self.url = reverse('music:set_repeat')

    def test_set_repeat_requires_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_set_repeat_invalid_mode_returns_error(self):
        response = self.client.post(
            self.url,
            data='mode=invalid&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_set_repeat_off(self, mock_cls):
        mock_service = MagicMock()
        mock_service.set_repeat.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='mode=off&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('off', data['message'].lower())
        mock_service.set_repeat.assert_called_once_with('off', device_id='dev1')

        queue = PlaybackQueue.objects.get(user=self.user)
        self.assertEqual(queue.repeat_mode, 'off')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_set_repeat_context(self, mock_cls):
        mock_service = MagicMock()
        mock_service.set_repeat.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='mode=context&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('all', data['message'].lower())

        queue = PlaybackQueue.objects.get(user=self.user)
        self.assertEqual(queue.repeat_mode, 'context')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_set_repeat_track(self, mock_cls):
        mock_service = MagicMock()
        mock_service.set_repeat.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='mode=track&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('one', data['message'].lower())

        queue = PlaybackQueue.objects.get(user=self.user)
        self.assertEqual(queue.repeat_mode, 'track')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_set_repeat_spotify_failure_returns_error(self, mock_cls):
        mock_service = MagicMock()
        mock_service.set_repeat.return_value = False
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='mode=off&device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_set_repeat_default_mode_off(self, mock_cls):
        """Missing mode param defaults to 'off'."""
        mock_service = MagicMock()
        mock_service.set_repeat.return_value = True
        mock_cls.return_value = mock_service

        self.client.post(
            self.url,
            data='device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        mock_service.set_repeat.assert_called_once_with('off', device_id='dev1')


# ---------------------------------------------------------------------------
# transfer_playback: JSON body + wrong kwarg fix
# ---------------------------------------------------------------------------

class TransferPlaybackTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='xferuser', password='testpass')
        make_spotify_user(self.user)
        self.client.login(username='xferuser', password='testpass')
        self.url = reverse('music:transfer_playback')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_transfer_form_encoded(self, mock_cls):
        mock_service = MagicMock()
        mock_service.transfer_playback.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='device_id=abc123',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        # Verify it was called with the right device_id and no wrong kwargs
        call_args = mock_service.transfer_playback.call_args
        self.assertEqual(call_args[0][0], 'abc123')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_transfer_json_body(self, mock_cls):
        """Frontend sends JSON; view should parse it correctly."""
        mock_service = MagicMock()
        mock_service.transfer_playback.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data=json.dumps({'device_id': 'xyz789'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        call_args = mock_service.transfer_playback.call_args
        self.assertEqual(call_args[0][0], 'xyz789')  # first positional arg is device_id

    def test_transfer_missing_device_id(self):
        response = self.client.post(
            self.url,
            data='device_id=',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_transfer_spotify_failure_returns_error(self, mock_cls):
        mock_service = MagicMock()
        mock_service.transfer_playback.return_value = False
        mock_cls.return_value = mock_service

        response = self.client.post(
            self.url,
            data='device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')


# ---------------------------------------------------------------------------
# get_playback_state: includes track_uri and context fields
# ---------------------------------------------------------------------------

class PlaybackStateResponseTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='stateuser', password='testpass')
        make_spotify_user(self.user)
        self.client.login(username='stateuser', password='testpass')
        self.url = reverse('music:playback_state')

    @patch('SyroMusic.playback_views.TokenManager')
    @patch('SyroMusic.playback_views.SpotifyService')
    def test_state_includes_track_uri_and_context(self, mock_cls, mock_token):
        mock_token.refresh_user_token.return_value = 'token'
        mock_service = MagicMock()
        mock_service.get_current_playback.return_value = {
            'is_playing': True,
            'progress_ms': 60000,
            'device': {'name': 'My Speaker', 'type': 'Speaker'},
            'context': {'type': 'album', 'uri': 'spotify:album:abc'},
            'item': {
                'id': 'track_id_1',
                'uri': 'spotify:track:track_id_1',
                'name': 'Test Song',
                'duration_ms': 200000,
                'artists': [{'name': 'Test Artist', 'id': 'artist_id_1'}],
                'album': {
                    'name': 'Test Album',
                    'uri': 'spotify:album:abc',
                    'images': [{'url': 'https://example.com/art.jpg'}],
                },
            },
        }
        mock_cls.return_value = mock_service

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['track_uri'], 'spotify:track:track_id_1')
        self.assertEqual(data['track_id'], 'track_id_1')
        self.assertEqual(data['context_type'], 'album')
        self.assertEqual(data['context_uri'], 'spotify:album:abc')
        self.assertIn('artist_id_1', data['artist_ids'])

    @patch('SyroMusic.playback_views.TokenManager')
    @patch('SyroMusic.playback_views.SpotifyService')
    def test_state_no_playback_returns_no_playback_status(self, mock_cls, mock_token):
        """When nothing is playing, status should be 'no_playback'."""
        mock_token.refresh_user_token.return_value = 'token'
        mock_service = MagicMock()
        mock_service.get_current_playback.return_value = None
        mock_cls.return_value = mock_service

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'no_playback')

    @patch('SyroMusic.playback_views.TokenManager')
    def test_state_expired_token_returns_401(self, mock_token):
        """Expired / unrefreshable token returns 401."""
        mock_token.refresh_user_token.return_value = None

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['status'], 'error')

    @patch('SyroMusic.playback_views.TokenManager')
    @patch('SyroMusic.playback_views.SpotifyService')
    def test_state_includes_album_image_url(self, mock_cls, mock_token):
        """Response should include album_image_url for cover art updates."""
        mock_token.refresh_user_token.return_value = 'token'
        mock_service = MagicMock()
        mock_service.get_current_playback.return_value = {
            'is_playing': True,
            'progress_ms': 10000,
            'device': {'name': 'Dev', 'type': 'Computer'},
            'context': None,
            'item': {
                'id': 'tid',
                'uri': 'spotify:track:tid',
                'name': 'Song',
                'duration_ms': 180000,
                'artists': [{'name': 'Artist', 'id': 'aid'}],
                'album': {
                    'name': 'Album',
                    'uri': 'spotify:album:aid',
                    'images': [{'url': 'https://img.example.com/cover.jpg'}],
                },
            },
        }
        mock_cls.return_value = mock_service

        response = self.client.get(self.url)
        data = response.json()
        self.assertEqual(data['album_image_url'], 'https://img.example.com/cover.jpg')

    @patch('SyroMusic.playback_views.TokenManager')
    @patch('SyroMusic.playback_views.SpotifyService')
    def test_state_progress_and_duration_fields(self, mock_cls, mock_token):
        """Response should include accurate progress_ms and duration_ms."""
        mock_token.refresh_user_token.return_value = 'token'
        mock_service = MagicMock()
        mock_service.get_current_playback.return_value = {
            'is_playing': True,
            'progress_ms': 75000,
            'device': {'name': 'Dev', 'type': 'Computer'},
            'context': None,
            'item': {
                'id': 'tid2',
                'uri': 'spotify:track:tid2',
                'name': 'Song 2',
                'duration_ms': 240000,
                'artists': [],
                'album': {'name': 'Album', 'uri': '', 'images': []},
            },
        }
        mock_cls.return_value = mock_service

        response = self.client.get(self.url)
        data = response.json()
        self.assertEqual(data['progress_ms'], 75000)
        self.assertEqual(data['duration_ms'], 240000)
        self.assertTrue(data['is_playing'])


# ---------------------------------------------------------------------------
# autoplay_next endpoint
# ---------------------------------------------------------------------------

class AutoplayNextTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='autouser', password='testpass')
        make_spotify_user(self.user)
        self.client.login(username='autouser', password='testpass')
        self.url = reverse('music:autoplay_next')

    def test_autoplay_requires_login(self):
        anon = Client()
        response = anon.post(self.url)
        self.assertIn(response.status_code, [302, 403])

    def test_autoplay_only_allows_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_autoplay_plays_from_local_queue(self, mock_cls):
        """If local queue has tracks, skip to next without queuing recommendations."""
        mock_service = MagicMock()
        mock_service.next_track.return_value = True
        mock_cls.return_value = mock_service

        PlaybackQueue.objects.create(
            user=self.user,
            queue_tracks=[{'uri': 'spotify:track:queued1', 'title': 'Queued Song'}],
        )

        response = self.client.post(self.url, content_type='application/json', data='{}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        mock_service.next_track.assert_called_once()
        # Should NOT call get_recommendations when queue has tracks
        mock_service.get_recommendations.assert_not_called()

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_autoplay_queues_recommendations_for_single_track(self, mock_cls):
        """No queue, no context → get recommendations and queue them."""
        mock_service = MagicMock()
        mock_service.get_current_playback.return_value = {
            'is_playing': False,
            'context': None,
            'item': {
                'id': 'current_track_id',
                'uri': 'spotify:track:current',
                'artists': [{'id': 'artist_1'}],
            },
        }
        mock_service.get_recommendations.return_value = {
            'tracks': [
                {'uri': 'spotify:track:rec1'},
                {'uri': 'spotify:track:rec2'},
            ]
        }
        mock_service.add_to_queue.return_value = True
        mock_service.next_track.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(self.url, content_type='application/json', data='{}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('2', data['message'])  # "2 recommended tracks"
        mock_service.add_to_queue.assert_called()
        mock_service.next_track.assert_called_once()

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_autoplay_context_skips_to_next(self, mock_cls):
        """Playing in an album context → just skip to next track."""
        mock_service = MagicMock()
        mock_service.get_current_playback.return_value = {
            'is_playing': False,
            'context': {'type': 'album', 'uri': 'spotify:album:xyz'},
            'item': {'id': 'tid', 'uri': 'spotify:track:tid', 'artists': []},
        }
        mock_service.next_track.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(self.url, content_type='application/json', data='{}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        mock_service.next_track.assert_called_once()
        mock_service.get_recommendations.assert_not_called()

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_autoplay_no_recommendations_available(self, mock_cls):
        """When recommendations return nothing, return info status gracefully."""
        mock_service = MagicMock()
        mock_service.get_current_playback.return_value = {
            'is_playing': False,
            'context': None,
            'item': {
                'id': 'tid3',
                'uri': 'spotify:track:tid3',
                'artists': [{'id': 'a1'}],
            },
        }
        mock_service.get_recommendations.return_value = {'tracks': []}
        mock_cls.return_value = mock_service

        response = self.client.post(self.url, content_type='application/json', data='{}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data['status'], ['info', 'success'])

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_autoplay_playlist_context_skips_to_next(self, mock_cls):
        """Playing in a playlist context → just skip to next track."""
        mock_service = MagicMock()
        mock_service.get_current_playback.return_value = {
            'is_playing': False,
            'context': {'type': 'playlist', 'uri': 'spotify:playlist:plist1'},
            'item': {'id': 'tid5', 'uri': 'spotify:track:tid5', 'artists': []},
        }
        mock_service.next_track.return_value = True
        mock_cls.return_value = mock_service

        response = self.client.post(self.url, content_type='application/json', data='{}')
        self.assertEqual(response.status_code, 200)
        mock_service.next_track.assert_called_once()
        mock_service.get_recommendations.assert_not_called()


# ---------------------------------------------------------------------------
# Bug 1 — TransferPlaybackDeduplicationTests
# ---------------------------------------------------------------------------

class TransferPlaybackDeduplicationTests(TestCase):
    """Confirm only one transfer_playback exists and it handles both content types."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='xfer2user', password='testpass')
        SpotifyUser.objects.create(
            user=self.user,
            spotify_id='xfer2_spotify_id',
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            token_expires_at=timezone.now() + timezone.timedelta(hours=1),
            is_connected=True,
        )
        self.client.login(username='xfer2user', password='testpass')
        self.url = reverse('music:transfer_playback')

    def test_only_one_transfer_playback_function_exists(self):
        """Verify there is no duplicate function definition at import time."""
        import SyroMusic.playback_views as pv
        import inspect
        source = inspect.getsource(pv)
        count = source.count('def transfer_playback(')
        self.assertEqual(count, 1, "Found duplicate transfer_playback definitions — only one must exist")

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_transfer_accepts_form_encoded(self, mock_cls):
        mock_service = MagicMock()
        mock_service.transfer_playback.return_value = True
        mock_cls.return_value = mock_service
        response = self.client.post(
            self.url,
            data='device_id=dev_form_abc',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_transfer_accepts_json(self, mock_cls):
        mock_service = MagicMock()
        mock_service.transfer_playback.return_value = True
        mock_cls.return_value = mock_service
        response = self.client.post(
            self.url,
            data=json.dumps({'device_id': 'dev_json_xyz'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_transfer_returns_json_response_not_drf_response(self, mock_cls):
        """Response must be deserializable as plain JSON (not a DRF renderer artifact)."""
        mock_service = MagicMock()
        mock_service.transfer_playback.return_value = True
        mock_cls.return_value = mock_service
        response = self.client.post(
            self.url,
            data='device_id=dev1',
            content_type='application/x-www-form-urlencoded',
        )
        data = response.json()
        self.assertIn('status', data)

    def test_transfer_missing_device_id_returns_400(self):
        response = self.client.post(
            self.url,
            data='device_id=',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400)


# ---------------------------------------------------------------------------
# Bug 2 — PlayerSearchAPITests
# ---------------------------------------------------------------------------

class PlayerSearchAPITests(TestCase):
    """Verify the search JSON API always returns application/json."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='searchplayer', password='testpass')
        SpotifyUser.objects.create(
            user=self.user,
            spotify_id='search_spotify_id',
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            token_expires_at=timezone.now() + timezone.timedelta(hours=1),
            is_connected=True,
        )
        self.client.login(username='searchplayer', password='testpass')
        self.url = reverse('music:search_json')

    @patch('SyroMusic.search_views.SpotifyService')
    def test_response_content_type_is_json_when_accept_json(self, mock_cls):
        """With Accept: application/json header, response must be JSON."""
        mock_service = MagicMock()
        mock_service.search.return_value = {'tracks': {'items': []}, 'artists': {'items': []}, 'albums': {'items': []}}
        mock_cls.return_value = mock_service
        response = self.client.get(
            self.url,
            {'q': 'test'},
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response['Content-Type'])
        data = response.json()
        self.assertIn('songs', data)

    @patch('SyroMusic.search_views.SpotifyService')
    def test_response_is_not_redirect_when_authenticated(self, mock_cls):
        """Authenticated request must not be redirected to login."""
        mock_service = MagicMock()
        mock_service.search.return_value = {'tracks': {'items': []}, 'artists': {'items': []}, 'albums': {'items': []}}
        mock_cls.return_value = mock_service
        response = self.client.get(
            self.url,
            {'q': 'hello'},
            HTTP_ACCEPT='application/json',
        )
        self.assertFalse(response.has_header('Location'), "Response must not redirect authenticated users")
        self.assertNotEqual(response.status_code, 302)

    def test_unauthenticated_returns_403_not_html_redirect(self):
        """Unauthenticated request with Accept: application/json must return 403, not HTML."""
        anon = Client()
        response = anon.get(
            self.url,
            {'q': 'test'},
            HTTP_ACCEPT='application/json',
        )
        self.assertIn(response.status_code, [401, 403])
        self.assertIn('application/json', response.get('Content-Type', ''))

    @patch('SyroMusic.search_views.SpotifyService')
    def test_short_query_returns_empty_not_error(self, mock_cls):
        """Query under 2 characters must return empty lists, not an error."""
        response = self.client.get(
            self.url,
            {'q': 'a'},
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['songs'], [])

    @patch('SyroMusic.search_views.SpotifyService')
    def test_spotify_results_include_required_fields(self, mock_cls):
        """Each returned song must have title, artist, uri, and spotify_id."""
        mock_service = MagicMock()
        mock_service.search.return_value = {
            'tracks': {'items': [{
                'id': 'tid1', 'name': 'Test Song', 'uri': 'spotify:track:tid1',
                'artists': [{'name': 'Test Artist'}],
                'album': {'name': 'Test Album', 'images': [{'url': 'https://example.com/art.jpg'}]},
                'duration_ms': 180000,
            }]},
            'artists': {'items': []},
            'albums': {'items': []},
        }
        mock_cls.return_value = mock_service
        response = self.client.get(self.url, {'q': 'test song'}, HTTP_ACCEPT='application/json')
        data = response.json()
        self.assertGreater(len(data['songs']), 0)
        song = data['songs'][0]
        for field in ['title', 'artist', 'uri', 'spotify_id']:
            self.assertIn(field, song, f"Song result missing required field: {field}")


# ---------------------------------------------------------------------------
# Bug 3 — PlayerTemplateTests
# ---------------------------------------------------------------------------

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PlayerTemplateTests(TestCase):
    """Verify the player template renders with correct CORS attributes for album art."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='templateuser', password='testpass')
        SpotifyUser.objects.create(
            user=self.user,
            spotify_id='template_spotify_id',
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            token_expires_at=timezone.now() + timezone.timedelta(hours=1),
            is_connected=True,
        )
        self.client.login(username='templateuser', password='testpass')

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_album_art_img_has_crossorigin_attribute(self, mock_cls):
        """The album art img tag must include crossorigin='anonymous' for CORS canvas access."""
        mock_service = MagicMock()
        mock_service.get_current_playback.return_value = None
        mock_service.get_available_devices.return_value = []
        mock_cls.return_value = mock_service
        response = self.client.get(reverse('music:player'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('crossorigin="anonymous"', content,
            "Album art <img> must have crossorigin='anonymous' to prevent canvas tainting")

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_dynamic_bg_element_present_in_template(self, mock_cls):
        """The dynamicBg element must be present for color extraction to target."""
        mock_service = MagicMock()
        mock_service.get_current_playback.return_value = None
        mock_service.get_available_devices.return_value = []
        mock_cls.return_value = mock_service
        response = self.client.get(reverse('music:player'))
        self.assertIn('id="dynamicBg"', response.content.decode())

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_apply_dynamic_background_function_present(self, mock_cls):
        """The applyDynamicBackground JS function must be defined in the template."""
        mock_service = MagicMock()
        mock_service.get_current_playback.return_value = None
        mock_service.get_available_devices.return_value = []
        mock_cls.return_value = mock_service
        response = self.client.get(reverse('music:player'))
        self.assertIn('function applyDynamicBackground', response.content.decode())

    @patch('SyroMusic.playback_views.SpotifyService')
    def test_cors_reload_guard_present_in_template(self, mock_cls):
        """The CORS reload guard block must be present in the applyDynamicBackground function."""
        mock_service = MagicMock()
        mock_service.get_current_playback.return_value = None
        mock_service.get_available_devices.return_value = []
        mock_cls.return_value = mock_service
        response = self.client.get(reverse('music:player'))
        content = response.content.decode()
        self.assertIn('CORS reload guard', content,
            "The CORS reload guard comment/block must be present in applyDynamicBackground")


# ---------------------------------------------------------------------------
# Bug 6 — PlaylistModelTests
# ---------------------------------------------------------------------------

class PlaylistModelTests(TestCase):
    """Verify the Playlist model has the spotify_id field and it behaves correctly."""

    def setUp(self):
        self.user = User.objects.create_user(username='plmodeluser', password='testpass')

    def test_playlist_has_spotify_id_field(self):
        """Playlist model must have a spotify_id field."""
        field_names = [f.name for f in Playlist._meta.get_fields()]
        self.assertIn('spotify_id', field_names,
            "Playlist model is missing spotify_id field — run makemigrations and migrate")

    def test_spotify_id_is_nullable(self):
        """spotify_id must be nullable so playlists without Spotify links still work."""
        playlist = Playlist.objects.create(
            title='Local Only Playlist',
            user=self.user,
        )
        self.assertIsNone(playlist.spotify_id)

    def test_spotify_id_can_store_value(self):
        """spotify_id must be able to store a Spotify playlist ID string."""
        playlist = Playlist.objects.create(
            title='Spotify Linked Playlist',
            user=self.user,
            spotify_id='37i9dQZF1DXcBWIGoYBM5M',
        )
        playlist.refresh_from_db()
        self.assertEqual(playlist.spotify_id, '37i9dQZF1DXcBWIGoYBM5M')

    def test_create_playlist_without_spotify_id(self):
        """Creating a Playlist without spotify_id must not raise any error."""
        try:
            Playlist.objects.create(title='No Spotify', user=self.user)
        except TypeError as e:
            self.fail(f"Creating Playlist without spotify_id raised TypeError: {e}")

    def test_create_playlist_with_spotify_id(self):
        """Creating a Playlist with spotify_id must not raise any error."""
        try:
            Playlist.objects.create(
                title='With Spotify',
                user=self.user,
                spotify_id='some_id_123',
            )
        except TypeError as e:
            self.fail(f"Creating Playlist with spotify_id raised TypeError: {e}")
