"""
Management command to sync tracks for albums from Spotify.
This fetches all tracks for each album in the database.

Usage:
    python manage.py sync_album_tracks
    python manage.py sync_album_tracks --limit 50
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from SyroMusic.models import SpotifyUser, Album, Artist, Song
from SyroMusic.services import SpotifyService
from django.db import IntegrityError
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync tracks for albums from Spotify'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of albums to process'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-sync even if album already has tracks'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']

        # Get a user with Spotify connected to use their service
        try:
            spotify_user = SpotifyUser.objects.filter(is_connected=True).first()
            if not spotify_user:
                self.stdout.write(self.style.ERROR('No connected Spotify users found'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error finding Spotify user: {str(e)}'))
            return

        service = SpotifyService(spotify_user)

        # Get albums that need tracks
        if force:
            albums = Album.objects.filter(cover_url__isnull=False).exclude(cover_url='')
        else:
            # Only albums without tracks
            albums = Album.objects.filter(songs__isnull=True).distinct()

        if limit:
            albums = albums[:limit]

        total = albums.count()
        self.stdout.write(self.style.SUCCESS(f'Found {total} albums to sync tracks for'))

        synced_count = 0
        failed_count = 0
        skipped_count = 0

        for idx, album in enumerate(albums, 1):
            try:
                self.stdout.write(f'[{idx}/{total}] {album.title} by {album.artist.name}')

                # We need to get the Spotify album ID by searching
                # Search for the album
                query = f'album:{album.title} artist:{album.artist.name}'
                try:
                    results = service.sp.search(q=query, type='album', limit=1)
                    if not results or not results.get('albums') or not results['albums'].get('items'):
                        self.stdout.write(self.style.WARNING(f'  Album not found on Spotify'))
                        skipped_count += 1
                        continue

                    spotify_album = results['albums']['items'][0]
                    spotify_album_id = spotify_album['id']

                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Search failed: {str(e)}'))
                    failed_count += 1
                    continue

                # Get tracks for this album
                tracks_result = service.get_album_tracks(spotify_album_id)
                if not tracks_result or not tracks_result.get('items'):
                    self.stdout.write(self.style.WARNING(f'  No tracks found'))
                    skipped_count += 1
                    continue

                track_count = 0
                for track_data in tracks_result['items']:
                    try:
                        track_name = track_data.get('name', 'Unknown Track')
                        track_number = track_data.get('track_number', 0)
                        duration_ms = track_data.get('duration_ms', 0)
                        spotify_id = track_data.get('id', '')
                        uri = track_data.get('uri', '')

                        # Check if track already exists
                        if Song.objects.filter(
                            title=track_name,
                            album=album,
                            track_number=track_number
                        ).exists():
                            continue

                        # Create song
                        Song.objects.create(
                            title=track_name,
                            album=album,
                            artist=album.artist,
                            track_number=track_number,
                            duration=timedelta(milliseconds=duration_ms),
                            duration_ms=duration_ms,
                            spotify_id=spotify_id,
                            uri=uri,
                        )
                        track_count += 1

                    except IntegrityError:
                        continue
                    except Exception as e:
                        logger.error(f"Error creating track: {str(e)}")
                        continue

                if track_count > 0:
                    synced_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Added {track_count} tracks'))
                else:
                    skipped_count += 1
                    self.stdout.write(self.style.WARNING(f'  No new tracks added'))

            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f'  Failed: {str(e)}'))
                continue

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'Track sync complete!'))
        self.stdout.write(self.style.SUCCESS(f'  ✓ Synced: {synced_count} albums'))
        if failed_count > 0:
            self.stdout.write(self.style.WARNING(f'  ✗ Failed: {failed_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'  - Skipped: {skipped_count}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
