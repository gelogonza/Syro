from django.apps import AppConfig
from decouple import config


class SyromusicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'SyroMusic'

    def ready(self):
        """Run migrations automatically on app startup in production."""
        if config('DJANGO_ENV', default='development') == 'production':
            try:
                from django.core.management import call_command
                from django.db import connection

                # Check if database is accessible and migrations haven't run
                with connection.cursor() as cursor:
                    try:
                        cursor.execute("SELECT 1 FROM django_migrations LIMIT 1")
                    except Exception:
                        # Table doesn't exist, run migrations
                        call_command('migrate', verbosity=0)
                        return

                # Database exists, check if SyroMusic tables exist
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT to_regclass('SyroMusic_spotifyuser')"
                    )
                    if cursor.fetchone()[0] is None:
                        # Table doesn't exist, run migrations
                        call_command('migrate', verbosity=0)
            except Exception as e:
                # Silently fail - migrations might already be running
                pass
