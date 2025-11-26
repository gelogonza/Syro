"""
Management command to sync albums from Spotify to populate The Crate.
Imports albums from: saved albums, playlists, and recently played tracks.

Usage:
    python manage.py sync_spotify_albums <username>
    python manage.py sync_spotify_albums --all
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from SyroMusic.models import SpotifyUser, Album, Artist, Song
from SyroMusic.services import SpotifyService
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync albums from Spotify to populate The Crate'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            nargs='?',
            type=str,
            help='Username to sync albums for'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sync albums for all users with Spotify connected'
        )

    def handle(self, *args, **options):
        username = options.get('username')
        sync_all = options.get('all')

        if not username and not sync_all:
            raise CommandError('Please provide a username or use --all flag')

        if sync_all:
            users = User.objects.filter(spotifyuser__isnull=False)
            self.stdout.write(f'Syncing albums for {users.count()} users...')
            for user in users:
                self.sync_user_albums(user)
        else:
            try:
                user = User.objects.get(username=username)
                self.sync_user_albums(user)
            except User.DoesNotExist:
                raise CommandError(f'User "{username}" does not exist')

    def sync_user_albums(self, user):
        """Sync albums for a specific user."""
        self.stdout.write(f'\nSyncing albums for user: {user.username}')

        try:
            spotify_user = SpotifyUser.objects.get(user=user)
        except SpotifyUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'  No Spotify account connected for {user.username}'))
            return

        service = SpotifyService(spotify_user)
        total_albums = 0

        # 1. Sync saved albums
        self.stdout.write('  Fetching saved albums...')
        saved_count = self.sync_saved_albums(service)
        total_albums += saved_count
        self.stdout.write(self.style.SUCCESS(f'    Added {saved_count} albums from saved library'))

        # 2. Sync albums from playlists
        self.stdout.write('  Fetching albums from playlists...')
        playlist_count = self.sync_playlist_albums(service)
        total_albums += playlist_count
        self.stdout.write(self.style.SUCCESS(f'    Added {playlist_count} albums from playlists'))

        # 3. Sync albums from recently played
        self.stdout.write('  Fetching albums from recently played...')
        recent_count = self.sync_recent_albums(service)
        total_albums += recent_count
        self.stdout.write(self.style.SUCCESS(f'    Added {recent_count} albums from recently played'))

        self.stdout.write(self.style.SUCCESS(f'\n  Total: {total_albums} albums synced for {user.username}'))

    def sync_saved_albums(self, service):
        """Sync user's saved albums from Spotify."""
        count = 0
        offset = 0
        limit = 50

        while True:
            results = service.get_saved_albums(limit=limit, offset=offset)
            if not results or not results.get('items'):
                break

            for item in results['items']:
                album_data = item.get('album')
                if album_data:
                    if self.create_album_from_spotify(album_data):
                        count += 1

            if not results.get('next'):
                break
            offset += limit

        return count

    def sync_playlist_albums(self, service):
        """Sync albums from user's playlists."""
        count = 0
        albums_seen = set()

        # Get user's playlists
        playlists_result = service.get_user_playlists(limit=50)
        if not playlists_result or not playlists_result.get('items'):
            return 0

        for playlist in playlists_result['items']:
            playlist_id = playlist.get('id')
            if not playlist_id:
                continue

            # Get tracks from playlist
            tracks_result = service.get_playlist_tracks(playlist_id, limit=100)
            if not tracks_result or not tracks_result.get('items'):
                continue

            for item in tracks_result['items']:
                track = item.get('track')
                if not track:
                    continue

                album_data = track.get('album')
                if album_data:
                    album_id = album_data.get('id')
                    if album_id and album_id not in albums_seen:
                        albums_seen.add(album_id)
                        if self.create_album_from_spotify(album_data):
                            count += 1

        return count

    def sync_recent_albums(self, service):
        """Sync albums from recently played tracks."""
        count = 0
        albums_seen = set()

        results = service.get_recently_played(limit=50)
        if not results or not results.get('items'):
            return 0

        for item in results['items']:
            track = item.get('track')
            if not track:
                continue

            album_data = track.get('album')
            if album_data:
                album_id = album_data.get('id')
                if album_id and album_id not in albums_seen:
                    albums_seen.add(album_id)
                    if self.create_album_from_spotify(album_data):
                        count += 1

        return count

    def create_album_from_spotify(self, album_data):
        """Create or update an album from Spotify data."""
        try:
            album_title = album_data.get('name', 'Unknown Album')
            if not album_title:
                return False

            # Get or create artist
            artist_data = album_data.get('artists', [{}])[0]
            artist_name = artist_data.get('name', 'Unknown Artist')

            artist, created = Artist.objects.get_or_create(
                name=artist_name
            )

            # Check if album already exists for this artist
            if Album.objects.filter(title=album_title, artist=artist).exists():
                return False

            # Get album cover image
            images = album_data.get('images', [])
            cover_url = images[0]['url'] if images else ''

            # Parse release date
            release_date_str = album_data.get('release_date', '2000-01-01')
            try:
                # Handle different date formats from Spotify
                if len(release_date_str) == 4:  # Just year
                    release_date = f"{release_date_str}-01-01"
                elif len(release_date_str) == 7:  # Year-month
                    release_date = f"{release_date_str}-01"
                else:
                    release_date = release_date_str
            except:
                release_date = '2000-01-01'

            # Create album
            album = Album.objects.create(
                title=album_title,
                artist=artist,
                release_date=release_date,
                cover_url=cover_url,
                spotify_id=album_data.get('id'),
            )

            return True

        except IntegrityError as e:
            # Album already exists
            return False
        except Exception as e:
            logger.error(f"Error creating album: {str(e)}")
            return False
