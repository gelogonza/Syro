"""
Management command to extract dominant colors from album covers.
This runs synchronously without requiring Celery/Redis.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from SyroMusic.models import Album
import io
import urllib.request
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Extract dominant colors from album cover artwork'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-extraction even if color already exists',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of albums to process',
        )

    def handle(self, *args, **options):
        force = options['force']
        limit = options['limit']

        self.stdout.write(self.style.SUCCESS('Starting album color extraction...'))

        # Get albums that need color extraction
        if force:
            albums = Album.objects.filter(cover_url__isnull=False).exclude(cover_url='')
        else:
            # Only albums without colors or with default color
            albums = Album.objects.filter(
                cover_url__isnull=False
            ).exclude(cover_url='').filter(
                dominant_color__in=['', '#1a1a2e']
            )

        if limit:
            albums = albums[:limit]

        total = albums.count()
        self.stdout.write(f'Found {total} albums to process')

        extracted_count = 0
        failed_count = 0
        skipped_count = 0

        for idx, album in enumerate(albums, 1):
            try:
                if not album.cover_url:
                    skipped_count += 1
                    continue

                self.stdout.write(f'[{idx}/{total}] Processing: {album.title} by {album.artist.name}')

                # Download album cover image
                try:
                    response = urllib.request.urlopen(album.cover_url, timeout=10)
                    img = Image.open(io.BytesIO(response.read())).convert('RGB')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Failed to download: {str(e)}'))
                    failed_count += 1
                    continue

                # Resize for faster processing
                img = img.resize((150, 150))

                # Extract dominant color using quantization
                pixels = list(img.getdata())
                color_map = {}

                for r, g, b in pixels:
                    # Quantize colors to reduce noise
                    r = (r // 25) * 25
                    g = (g // 25) * 25
                    b = (b // 25) * 25
                    key = (r, g, b)
                    color_map[key] = color_map.get(key, 0) + 1

                # Find most frequent color with good brightness
                dominant_color = '#1a1a2e'  # default
                max_count = 0

                for (r, g, b), count in color_map.items():
                    brightness = (r * 299 + g * 587 + b * 114) / 1000
                    # Filter out very dark or very light colors
                    if count > max_count and 20 < brightness < 240:
                        max_count = count
                        dominant_color = f'#{r:02x}{g:02x}{b:02x}'

                # Save color to database
                album.dominant_color = dominant_color
                album.color_extracted_at = timezone.now()
                album.save(update_fields=['dominant_color', 'color_extracted_at'])

                extracted_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Extracted color: {dominant_color}'))

            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f'  Failed: {str(e)}'))
                continue

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'Color extraction complete!'))
        self.stdout.write(self.style.SUCCESS(f'  ✓ Extracted: {extracted_count}'))
        if failed_count > 0:
            self.stdout.write(self.style.WARNING(f'  ✗ Failed: {failed_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'  - Skipped: {skipped_count}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
